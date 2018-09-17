import argparse
import logging
import os

from distutils.spawn import find_executable

from .base import BaseSubcommand

from compose_flow import errors


class PassthroughBaseSubcommand(BaseSubcommand):
    command_name = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def fill_subparser(cls, parser, subparser) -> None:
        subparser.add_argument('extra_args', nargs=argparse.REMAINDER)

    def get_command(self):
        # check to make sure the command is installed
        command_path = find_executable(self.command_name)
        if command_path is None:
            raise errors.ErrorMessage(f'{self.command_name} not found in PATH; is it installed?')

        return [command_path]

    def handle(self, extra_args:list=None) -> [None, str]:
        command = self.get_command()

        args = self.workflow.args

        extra_args = extra_args or args.extra_args
        command.extend(extra_args)

        command_s = ' '.join(command)

        self.logger.info(command_s)

        if not args.dry_run:
            self.execute(command_s)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')
