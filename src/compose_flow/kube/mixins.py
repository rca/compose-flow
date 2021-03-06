"""
Compose subcommand
"""
from functools import lru_cache
import os
import pathlib
import sh
import yaml


from compose_flow.errors import InvalidTargetClusterError, MissingManifestError, ManifestCheckError
from compose_flow.config import get_config
from compose_flow.kube.checks import BaseChecker, ManifestChecker, AnswersChecker
from compose_flow.utils import render, render_jinja

CLUSTER_LS_FORMAT = '{{.Cluster.Name}}: {{.Cluster.ID}}'
PROJECT_LS_FORMAT = '{{.Project.Name}}: {{.Project.ID}}'

EXCLUDE_PROFILES = ['local']

NONFATAL_ERROR_MESSAGES = ['strconv.ParseFloat: parsing "']


class KubeMixIn(object):
    """
    Mix-in for generic Kubernetes CLI interactions
    """

    kubectl_command = 'rancher kubectl'

    @property
    @lru_cache()
    def config(self):
        return get_config()

    @property
    def rancher_config(self):
        return self.config['rancher']

    def get_app_deploy_command(self, app: dict, target: str = 'rancher') -> str:
        '''
        Construct command to install or upgrade a Rancher app
        depending on whether or not it is already deployed.
        '''

        app_name = app['name']
        version = app['version']
        namespace = app['namespace']
        chart = app['chart']
        raw = app.get('raw', False)

        rendered_path = self.render_answers(app['answers'], app_name, raw)

        app_list = getattr(self, f'list_{target}_apps')()
        upgrade_command_method = getattr(self, f'get_{target}_app_upgrade_command')
        install_command_method = getattr(self, f'get_{target}_app_install_command')

        if app_name in app_list:
            return upgrade_command_method(app_name, rendered_path, chart, version)
        else:
            return install_command_method(app_name, rendered_path, namespace, chart, version)

    def list_helm_apps(self) -> str:
        return str(self.execute("helm ls -q --all")).split('\n')

    def get_helm_app_install_command(
            self, app_name: str, rendered_path: str,
            namespace: str, chart: str, version: str):
        return f'helm install --name {app_name} -f {rendered_path} --namespace {namespace} --version {version} {chart}'

    def get_helm_app_upgrade_command(self, app_name: str, rendered_path: str, chart: str, version: str):
        return f'helm upgrade {app_name} {chart} -f {rendered_path} --version {version}'

    def list_rancher_apps(self) -> str:
        return str(self.execute("rancher apps ls --format '{{.App.Name}}'")).split('\n')

    def get_rancher_app_install_command(
            self, app_name: str, rendered_path: str,
            namespace: str, chart: str, version: str):
        return f'rancher apps install --answers {rendered_path} --namespace {namespace} --version {version} {chart} {app_name}'

    def get_rancher_app_upgrade_command(self, app_name: str, rendered_path: str, chart: str, version: str):
        return f'rancher apps upgrade --answers {rendered_path} {app_name} {version}'

    def get_kubectl_command(self, manifest: dict, kubectl_prefix: str = 'kubectl') -> str:
        '''Construct command to apply a Kubernetes YAML manifest using kubectl.'''

        deploy_label = self.workflow.args.config_name

        raw_path = manifest['path']
        deploy_label = manifest.get('label')
        namespace = manifest.get('namespace')
        action = manifest.get('action', 'apply')
        raw = manifest.get('raw', False)

        namespace_str = f'--namespace {namespace} ' if namespace else ''
        deploy_label_str = '-l deploy={deploy_label} --prune ' if deploy_label else ''

        command = f'{kubectl_prefix} {namespace_str}{action} {deploy_label_str}--validate -f '

        if os.path.isdir(raw_path):
            rendered_path = self.render_nested_manifests(raw_path, raw)
            command += rendered_path + ' --recursive'
        elif os.path.isfile(raw_path):
            rendered_path = self.render_manifest(raw_path, raw)
            command += rendered_path
        else:
            raise MissingManifestError("Missing manifest at path: {}".format(manifest))

        return command

    def get_rke_deploy_command(self):
        raw_config = get_config()['rke']['config']
        rendered_config = f'compose-flow-{self.workflow.args.profile}-rke.yml'
        self.render_single_yaml(raw_config, rendered_config)
        return f'rke up --config {rendered_config}'

    def get_extra_section(self, section: str) -> list:
        extras = self.rancher_config.get('extras')
        if extras:
            env_extras = extras.get(self.workflow.args.profile)
            if env_extras:
                return env_extras.get(section, [])

        return []

    def get_helm_apps(self) -> list:
        return self.config['helm']

    def get_apps(self) -> list:
        default_apps = self.rancher_config.get('apps', [])
        extra_apps = self.get_extra_section('apps')

        return default_apps + extra_apps

    def get_kubectl_manifests(self) -> list:
        return self.config.get('kubectl_manifests', [])

    def get_rancher_manifests(self) -> list:
        default_manifests = self.rancher_config.get('manifests', [])
        extra_manifests = self.get_extra_section('manifests')

        return default_manifests + extra_manifests

    def get_manifest_filename(self, manifest_path: str) -> str:
        escaped_path = (
            manifest_path
            .replace('../', '')
            .replace('./', '')
            .replace('/', '-')
            .replace('.yaml', '.yml')
            .rstrip('-')
        )
        return f'compose-flow-{self.cluster_name}-manifest-{escaped_path}'

    def get_answers_filename(self, app_name: str) -> str:
        return f'compose-flow-{self.cluster_name}-{app_name}-answers.yml'

    def render_single_yaml(self, input_path: str, output_path: str,
                           checker: BaseChecker = None, raw: bool = False
                           ) -> None:
        '''
        Read in single YAML file from specified path, render environment variables,
        then write out to a known location in the working dir.
        '''
        self.logger.info("Rendering YAML at %s to %s", input_path, output_path)

        with open(input_path, 'r') as fh:
            content = fh.read()

        if not raw:
            rendered = render(content, env=self.workflow.environment.data)
            rendered = render_jinja(rendered, env=self.workflow.environment.data)
        else:
            rendered = content

        if checker:
            errors = checker.check(rendered)

            if errors:
                raise ManifestCheckError('\n'.join(errors))

        with open(output_path, 'w') as fh:
            fh.write(rendered)

    @lru_cache()
    def render_manifest(self, manifest_path: str, raw: bool) -> str:
        '''Render the specified manifest YAML and return the path to the rendered file.'''
        rendered_path = self.get_manifest_filename(manifest_path)
        self.render_single_yaml(manifest_path, rendered_path, ManifestChecker(), raw)

        return rendered_path

    @lru_cache()
    def render_nested_manifests(self, dir_path: str, raw: bool) -> str:
        directory = pathlib.Path(dir_path)
        manifests = directory.glob('**/*.y*ml')
        rendered_path = self.get_manifest_filename(dir_path)

        for manifest in manifests:
            render_dest = os.path.join(
                rendered_path,
                str(manifest).lstrip(dir_path)
            )
            print(render_dest)
            parent_dest = os.path.dirname(render_dest)

            os.makedirs(parent_dest, mode=0o750, exist_ok=True)
            self.render_single_yaml(manifest, render_dest, ManifestChecker(), raw)
        return rendered_path

    @lru_cache()
    def render_answers(self, answers_path: str, app_name: str, raw: bool) -> str:
        '''Render the specified manifest YAML and return the path to the rendered file.'''
        rendered_path = self.get_answers_filename(app_name)
        self.render_single_yaml(answers_path, rendered_path, AnswersChecker(), raw)

        return rendered_path

    # Native Kube context management logic
    def switch_kube_context(self):
        '''
        Switch current kubectl context to target specified cluster based on environment
        '''
        profile_name = self.workflow.args.profile
        context_mapping = self.config.get('kubecontexts', {})

        target_context = context_mapping.get(profile_name, profile_name)
        try:
            self.execute(f'kubectl config use-context {target_context}')
        except sh.ErrorReturnCode_1:
            raise InvalidTargetClusterError("No context is defined for profile {}!\n\n"
                                            "Please specify a corresponding context in your kubeconfig file "
                                            "or map this profile name to an existing context "
                                            "in the 'kubecontexts' section of compose-flow.yml".format(profile_name))

    # Rancher context management logic
    @property
    @lru_cache()
    def cluster_listing(self):
        cluster_ls_command = f"rancher cluster ls --format '{CLUSTER_LS_FORMAT}'"
        output = str(self.execute(cluster_ls_command)).strip()
        for err in NONFATAL_ERROR_MESSAGES:
            if err in output:
                output = output.replace(err, '')
        return yaml.load(output)

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

    def switch_rancher_context(self):
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
