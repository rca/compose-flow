import logging
import os
import shlex

from .base import BaseSubcommand


class Deploy(BaseSubcommand):
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
