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
        pass

    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def handle(self):
        args = self.workflow.args
        env = self.workflow.environment
        profile = self.workflow.profile

        command = f"""docker stack deploy
          --prune
          --with-registry-auth
          --compose-file {profile.filename}
          {args.config_name}"""

        self.logger.info(command)

        if not args.dry_run:
            self.execute(command)

            env.write()
