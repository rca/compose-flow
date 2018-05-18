import logging
import os
import shlex

import sh

from .base import BaseSubcommand


class Deploy(BaseSubcommand):
    """
    Subcommand for deploying an image to the docker swarm
    """
    @classmethod
    def fill_subparser(cls, parser, subparser):
        pass

    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def handle(self):
        # check the profile to make sure it defines all the needed environment variables
        self.profile.check()

        command = f"""docker stack deploy
          --prune
          --with-registry-auth
          --compose-file {self.profile.filename}
          {self.env.env_name}"""

        command_split = shlex.split(command)

        self.logger.info(command)

        if not self.args.dry_run:
            executable = getattr(sh, command_split[0])
            executable(*command_split[1:], _env=os.environ)
