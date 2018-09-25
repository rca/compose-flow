"""
Compose subcommand
"""
from .passthrough_base import PassthroughBaseSubcommand
import yaml
import sh
import os
from compose_flow.config import get_config
from compose_flow import shell

CLUSTER_LS_FORMAT = '{{.Cluster.Name}}: {{.Cluster.ID}}'
PROJECT_LS_FORMAT = '{{.Project.Name}}: {{.Project.ID}}'


class RancherMixIn(object):
    """
    Mix-in for managing Rancher CLI context
    """

    def get_rancher_config_section(self):
        config = get_config()
        return config['rancher']

    def switch_context(self):
        '''
        Switch Rancher CLI context to target specified cluster based on environment
        and specified project name from compose-flow.yml
        '''
        # Get the cluster ID for the specified target environment
        cluster_ls_command = self.command_name + f" cluster ls --format '{CLUSTER_LS_FORMAT}'"
        clusters = yaml.load(str(self.execute(cluster_ls_command)))

        target_cluster_name = self.workflow.args.environment
        target_cluster_id = clusters[target_cluster_name]

        # Get the project name specified in compose-flow.yml
        rancher_config = self.get_rancher_config_section()
        target_project_name = rancher_config['project']

        base_context_switch_command = self.command_name + " context switch "
        name_context_switch_command = base_context_switch_command + target_project_name
        try:
            self.logger.info(name_context_switch_command)
            self.execute(name_context_switch_command)
        except sh.ErrorReturnCode_1 as exc:  # pylint: disable=E1101
            stderr = exc.stderr
            if 'Multiple resources of type project found for name' in stderr:
                # Choose the one that matches target cluster ID
                opts = stderr[stderr.find(b'[')+1:stderr.find(b']')]
                target_project_id = str([o for o in opts if target_cluster_id in o][0])

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
        if app.name in apps:
            return f'rancher apps upgrade --answers {app.answers} {app.name} {app.version}'
        else:
            return f'rancher apps install --answers {app.answers} --namespace {app.namespace} --version {app.version} {app.chart} {app.name}'

    def get_manifest_deploy_command(self, manifest_path: str) -> str:
        '''Construct command to apply a Kubernetes YAML manifest using the Rancher CLI.'''
        return f'rancher kubectl apply -f {manifest_path}'

    def get_apps(self) -> list:
        rancher_config = self.get_rancher_config_section()
        return rancher_config.get('apps', [])

    def get_manifests(self) -> list:
        rancher_config = self.get_rancher_config_section()
        return rancher_config.get('manifests', [])
