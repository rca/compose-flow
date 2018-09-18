"""
Compose subcommand
"""
from .passthrough_base import PassthroughBaseSubcommand
import yaml
import sh
from compose_flow.config import get_config

CLUSTER_LS_FORMAT = '{{.Cluster.Name}}: {{.Cluster.ID}}'
PROJECT_LS_FORMAT = '{{.Project.Name}}: {{.Project.ID}}'


class Rancher(PassthroughBaseSubcommand):
    """
    Subcommand for running docker commands
    """

    command_name = 'rancher'

    setup_environment = True

    setup_profile = False

    def switch_context(self):
        '''
        Switch Rancher CLI context to target specified cluster based on environment
        and specified project name from compose-flow.yml
        '''
        # Get the cluster ID for the specified target environment
        cluster_ls_command = self.command_name + f" cluster ls --format '{CLUSTER_LS_FORMAT}'"
        clusters = yaml.load(self.execute(cluster_ls_command))

        target_cluster_name = self.workflow.args.environment
        target_cluster_id = clusters[target_cluster_name]

        # Get the project name specified in compose-flow.yml
        config = get_config()
        target_project_name = config['rancher']['project']

        base_context_switch_command = self.command_name + " context switch "
        name_context_switch_command = base_context_switch_command + target_project_name
        try:
            self.execute(name_context_switch_command)
        except sh.ErrorReturnCode_1 as exc:  # pylint: disable=E1101
            stderr = exc.stderr
            if 'Multiple resources of type project found for name' in stderr:
                # Choose the one that matches target cluster ID
                opts = stderr[stderr.find(b'[')+1:stderr.find(b']')]
                target_project_id = str([o for o in opts if target_cluster_id in o][0])

                id_context_switch_command = base_context_switch_command + target_project_id
                self.execute(id_context_switch_command)
            else:
                raise

    def handle(self):
        self.switch_context()

        super().handle()
