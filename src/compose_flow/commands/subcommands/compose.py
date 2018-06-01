"""
Compose subcommand
"""
import argparse
import logging

from .passthrough_base import PassthroughBaseSubcommand

from compose_flow import docker, errors


class Compose(PassthroughBaseSubcommand):
    """
    Subcommand for running compose commands
    """
    command_name = 'docker-compose'
    dirty_working_copy_okay = True

    def get_command(self):
        command = super().get_command()

        command.extend([
            '--project-name', self.env.env_name,
            '-f', self.profile.filename,
        ])

        return command

    def handle(self, extra_args: list=None) -> [None, str]:
        # check the profile to make sure it defines all the needed environment variables
        self.profile.check()

        super().handle(extra_args=extra_args)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')
