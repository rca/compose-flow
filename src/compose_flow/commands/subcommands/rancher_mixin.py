"""
Compose subcommand
"""
import yaml
import sh
import os

from functools import lru_cache

from compose_flow.config import get_config
from compose_flow.utils import render, yaml_load, yaml_dump

CLUSTER_LS_FORMAT = '{{.Cluster.Name}}: {{.Cluster.ID}}'
PROJECT_LS_FORMAT = '{{.Project.Name}}: {{.Project.ID}}'

EXCLUDE_PROFILES = ['local']


class InvalidTargetClusterError(Exception):
    pass


class RancherMixIn(object):
    """
    Mix-in for managing Rancher CLI context
    """

    @property
    @lru_cache()
    def rancher_config(self):
        config = get_config()
        return config['rancher']

    @property
    @lru_cache()
    def cluster_listing(self):
        cluster_ls_command = f"rancher cluster ls --format '{CLUSTER_LS_FORMAT}'"
        return yaml.load(str(self.execute(cluster_ls_command)).strip())


    @property
    def cluster_name(self):
        '''
        Get the cluster name for the specified target environment.

        If profile_name is in the compose-flow.yml Rancher cluster mapping,
        use its value - otherwise use workflow.args.profile
        '''
        profile_name = self.workflow.args.profile
        cluster_mapping = self.rancher_config.get('clusters', {})

        if profile_name in EXCLUDE_PROFILES:
            raise InvalidTargetClusterError(
                "Invalid profile '{0}' for default cluster logic - please "
                "specify an explicit cluster mapping in compose-flow.yml and "
                "use a profile other than '{0}'".format(profile_name))

        return cluster_mapping.get(profile_name, profile_name)

    @property
    def cluster_id(self):
        return self.cluster_listing[self.cluster_name]

    def switch_context(self):
        '''
        Switch Rancher CLI context to target specified cluster based on environment
        and specified project name from compose-flow.yml
        '''
        # Get the project name specified in compose-flow.yml
        target_project_name = self.rancher_config['project']

        base_context_switch_command = "rancher context switch "
        name_context_switch_command = base_context_switch_command + target_project_name
        try:
            self.logger.info(name_context_switch_command)
            self.execute(name_context_switch_command)
        except sh.ErrorReturnCode_1 as exc:  # pylint: disable=E1101
            stderr = str(exc.stderr)
            if 'Multiple resources of type project found for name' in stderr:
                self.logger.info(
                    "Multiple clusters have a project called %s - "
                    "switching context by Project ID", target_project_name
                )
                # Choose the one that matches target cluster ID
                opts = stderr[stderr.find('[')+1:stderr.find(']')].split(' ')
                target_project_id = [o for o in opts if self.cluster_id in o][0]

                id_context_switch_command = base_context_switch_command + target_project_id
                self.logger.info(id_context_switch_command)
                self.execute(id_context_switch_command)
            else:
                raise

    def get_app_deploy_command(self, app: dict) -> str:
        '''
        Construct command to install or upgrade a Rancher app
        depending on whether or not it is already deployed.
        '''
        apps = str(self.execute("rancher apps ls --format '{{.App.Name}}'"))
        app_name = app['name']
        version = app['version']
        namespace = app['namespace']
        chart = app['chart']

        rendered_path = self.render_answers(app['answers'], app_name)
        if app_name in apps:
            return f'rancher apps upgrade --answers {rendered_path} {app_name} {version}'
        else:
            return f'rancher apps install --answers {rendered_path} --namespace {namespace} --version {version} {chart} {app_name}'

    def get_manifest_deploy_command(self, manifest_path: str) -> str:
        '''Construct command to apply a Kubernetes YAML manifest using the Rancher CLI.'''
        rendered_path = self.render_manifest(manifest_path)
        return f'rancher kubectl apply --validate -f {rendered_path}'

    def get_extra_section(self, section: str) -> list:
        extras = self.rancher_config.get('extras')
        if extras:
            env_extras = extras.get(self.workflow.args.profile)
            if env_extras:
                return env_extras.get(section, [])

        return []

    def get_apps(self) -> list:
        default_apps = self.rancher_config.get('apps', [])
        extra_apps = self.get_extra_section('apps')

        return default_apps + extra_apps

    def get_manifests(self) -> list:
        default_manifests = self.rancher_config.get('manifests', [])
        extra_manifests = self.get_extra_section('manifests')

        return default_manifests + extra_manifests

    def get_manifest_filename(self, manifest_path: str) -> str:
        args = self.workflow.args
        escaped_path = manifest_path.replace('../', '').replace('./', '').replace('/', '-').replace('.yaml', '.yml')
        return f'compose-flow-{args.profile}-manifest-{escaped_path}'

    def get_answers_filename(self, app_name: str) -> str:
        args = self.workflow.args
        return f'compose-flow-{args.profile}-{app_name}-answers.yml'

    def render_single_yaml(self, input_path: str, output_path: str) -> None:
        '''
        Read in single YAML file from specified path, render environment variables,
        then write out to a known location in the working dir.
        '''
        self.logger.info("Rendering YAML at %s to %s", input_path, output_path)

        # TODO: Add support for multiple YAML documents in a single file
        with open(input_path, 'r') as fh:
            try:
                content = yaml_load(fh)
            except yaml.composer.ComposerError:
                self.logger.exception("Each manifest file must contain a single YAML document!")
                raise

        rendered = render(yaml_dump(content), env=self.workflow.environment.data)

        with open(output_path, 'w') as fh:
            fh.write(rendered)

    @lru_cache()
    def render_manifest(self, manifest_path: str) -> str:
        '''Render the specified manifest YAML and return the path to the rendered file.'''
        rendered_path = self.get_manifest_filename(manifest_path)
        self.render_single_yaml(manifest_path, rendered_path)

        return rendered_path

    @lru_cache()
    def render_answers(self, answers_path: str, app_name: str) -> str:
        '''Render the specified manifest YAML and return the path to the rendered file.'''
        rendered_path = self.get_answers_filename(app_name)
        self.render_single_yaml(answers_path, rendered_path)

        return rendered_path
