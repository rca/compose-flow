"""
Compose subcommand
"""
import argparse
import logging
import os
import sys

import sh

from .base import BaseSubcommand
from .profile import Profile

from dc_workflows import docker

from distutils.spawn import find_executable


class Compose(BaseSubcommand):
    """
    Subcommand for running compose commands
    """
    def __init__(self, *args, **kwargs):
        # pop off the compose_args kwarg
        compose_args = kwargs.pop('compose_args', None)

        super().__init__(*args, **kwargs)

    @classmethod
    def fill_subparser(cls, parser, subparser) -> None:
        subparser.add_argument('compose_args', nargs=argparse.REMAINDER)

    def handle(self, compose_args:list=None) -> [None, str]:
        profile = Profile(self.workflow)
        profile.write()

        command = ['docker-compose']
        command[0] = find_executable(command[0])

        command.extend([
            '--project-name', self.args.project_name,
            '-f', profile.filename,
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
