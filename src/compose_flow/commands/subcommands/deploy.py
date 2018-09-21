import logging
import os
import shlex

from .base import BaseSubcommand
from .rancher_mixin import RancherMixIn


class Deploy(BaseSubcommand, RancherMixIn):
    """
    Subcommand for deploying an image to the docker swarm
    """
    rw_env = True
    update_version_env_vars = True

    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action', nargs='?', default='docker')

    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def build_docker_command(self):
        return f"""docker stack deploy
            --prune
            --with-registry-auth
            --compose-file {self.workflow.profile.filename}
            {self.workflow.args.config_name}"""

    def build_rancher_command(self):
        self.switch_context()

        command = ''

        for app in self.get_apps():
            # check if app is already installed - if so upgrade, if not install
            continue

        for manifest in self.get_manifests():
            command += 'rancher kubectl apply -f {}\n'.format(manifest)

        return command

    def handle(self):
        args = self.workflow.args
        env = self.workflow.environment
        action = args.action

        try:
            action_method = getattr(self, 'build_' + action + '_command')
        except AttributeError:
            self.logger.error("Unknown deployment platform: %s", action)

        command = action_method()

        self.logger.info(command)

        if not args.dry_run:
            self.execute(command)

            env.write()
