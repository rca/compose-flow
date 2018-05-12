"""
Compose subcommand
"""
import argparse
import logging
import os
import sys

import sh

from .base import BaseSubcommand
from .env import Env
from .profile import Profile

from dc_workflows import docker

from distutils.spawn import find_executable


class Compose(BaseSubcommand):
    """
    Subcommand for running compose commands
    """
    @classmethod
    def fill_subparser(cls, parser, subparser) -> None:
        subparser.add_argument('docker_args', nargs=argparse.REMAINDER)

    def handle(self):
        profile = Profile(self.workflow)
        profile.write()

        command = ['docker-compose']
        command[0] = find_executable(command[0])

        command.extend([
            '--project-name', self.args.project_name,
            '-f', profile.filename,
        ])

        command.extend(self.args.docker_args)

        self.logger.info(' '.join(command))

        if not self.args.dry_run:
            # os.execve(command[0], command, os.environ)
            proc = getattr(sh, command[0])
            proc(*command[1:], _env=os.environ, _fg=True)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')
