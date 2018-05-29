"""
Compose subcommand
"""
import argparse
import logging
import os
import sys

import sh

from .base import BaseSubcommand

from compose_flow import docker

from distutils.spawn import find_executable


class Compose(BaseSubcommand):
    """
    Subcommand for running compose commands
    """
    dirty_working_copy_okay = True

    def __init__(self, *args, **kwargs):
        # pop off the compose_args kwarg
        compose_args = kwargs.pop('compose_args', None)

        super().__init__(*args, **kwargs)

    @classmethod
    def fill_subparser(cls, parser, subparser) -> None:
        subparser.add_argument('compose_args', nargs=argparse.REMAINDER)

    def handle(self, compose_args:list=None) -> [None, str]:
        # check the profile to make sure it defines all the needed environment variables
        self.profile.check()

        command = ['docker-compose']
        command[0] = find_executable(command[0])

        command.extend([
            '--project-name', self.env.env_name,
            '-f', self.profile.filename,
        ])

        compose_args = compose_args or self.args.compose_args
        command.extend(compose_args)

        self.logger.info(' '.join(command))

        if not self.args.dry_run:
            # os.execve(command[0], command, os.environ)
            proc = getattr(sh, command[0])
            proc(*command[1:], _env=os.environ, _fg=True)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')
