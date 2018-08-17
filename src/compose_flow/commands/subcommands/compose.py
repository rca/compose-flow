"""
Compose subcommand
"""
import argparse
import logging
import os

from .passthrough_base import PassthroughBaseSubcommand

from compose_flow import docker, errors

DEFAULT_COMPOSE_FILENAME = 'docker-compose.yml'


class Compose(PassthroughBaseSubcommand):
    """
    Subcommand for running compose commands
    """
    command_name = 'docker-compose'
    dirty_working_copy_okay = True

    def __init__(self, *args, **kwargs):
        self.check_profile = kwargs.pop('check_profile', True)
        self._version = kwargs.pop('version', None)

        super().__init__(*args, **kwargs)

    def get_command(self):
        command = super().get_command()

        if self.env.env_name:
            command.extend(['--project-name', self.env.project_name])

        # add -f when an overlay file is created
        if self.overlay:
            command.extend([
                '-f', self.profile.filename,
            ])

        return command

    def handle(self, extra_args: list=None) -> [None, str]:
        # check the profile to make sure it defines all the needed environment variables
        if self.check_profile:
            self.profile.check()

        # check to see if Dockerfile uses the VERSION build arg
        has_version_arg = False
        try:
            with open('../Dockerfile', 'r') as fh:
                while True:
                    line = fh.readline()
                    if line == '':
                        break
                    line = line.strip()

                    if 'ARG VERSION' in line:
                        has_version_arg = True
                        break
        except FileNotFoundError:
            self.logger.warning("Failed to find Dockerfile, not using build args.")
            pass

        extra_args = extra_args or self.args.extra_args
        if has_version_arg and extra_args[0] == 'build' and '--build-arg' not in extra_args:
            extra_args.extend(['--build-arg', f'VERSION={self.version}'])

        super().handle(extra_args=extra_args)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    @property
    def version(self):
        """
        Returns the version in the environment, unless it was overridden in this Compose instance
        """
        return self._version or self.env.version
