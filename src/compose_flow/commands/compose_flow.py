"""
    ,---,. ,--,
  ,'  .' ,--.'|
,---.'   |  | :     ,---.          .---.
|   |   .:  : '    '   ,'\\        /. ./|
:   :  : |  ' |   /   /   |    .-'-. ' |
:   |  |-'  | |  .   ; ,. :   /___/ \\: |
|   :  ;/|  | :  '   | |: :.-'.. '   ' .
|   |   .'  : |__'   | .; /___/ \\:     '
'   :  ' |  | '.'|   :    .   \\  ' .\\
|   |  | ;  :    ;\\   \\  / \\   \\   ' \\ |
|   :  \\ |  ,   /  `----'   \\   \\  |--"
|   | ,'  ---`-'             \\   \\ |
`----'                        '---"

Compose Flow - Codified workflows for Docker Compose and Swarm

This utility is built on top of Docker Compose and Swarm Mode. It establishes
conventions for publishing Images, deploying Stacks across multiple
installations (like separate dev and prod Swarms), and working with service
containers that are easily shared between team members -- and bots -- who need
to manage running services.
"""
import argparse
import os
import sys

from .subcommands import find_subcommands, set_default_subparser
from ..config import DC_CONFIG_ROOT
from ..errors import CommandError, ErrorMessage

PROJECT_NAME = os.path.basename(os.getcwd())


class ComposeFlow(object):
    def __init__(self, argv=None):
        self.argv = argv or sys.argv[1:]

        self.parser = self.get_argument_parser()
        self.args, self.args_remainder = self.parser.parse_known_args(self.argv)

        # the subcommand that is being run; defined in run() below
        self.subcommand = None

        if os.path.exists(DC_CONFIG_ROOT):
            os.chdir(DC_CONFIG_ROOT)

    def get_argument_parser(self, doc: str=None):
        argparse.ArgumentParser.set_default_subparser = set_default_subparser

        doc = doc or __doc__

        parser = argparse.ArgumentParser(
            epilog=doc,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument('-e', '--environment')
        parser.add_argument('-p', '--profile')
        parser.add_argument(
            '--noop', '--dry-run',
            action='store_true', dest='dry_run',
            help='just print command, do not execute'
        )
        parser.add_argument(
            '-n', '--project-name',
            default=PROJECT_NAME,
            help=f'the project name to use, default={PROJECT_NAME}'
        )

        self.subparsers = parser.add_subparsers(dest='command')

        for subcommand in find_subcommands():
            subcommand.setup_subparser(parser, self.subparsers)

        parser.set_default_subparser('help')

        return parser

    def run(self):
        self.subcommand = self.args.subcommand_cls(self)

        try:
            return self.subcommand.run()
        except CommandError as exc:
            self.parser.print_help()

            return f'\n{exc}'
        except ErrorMessage as exc:
            return f'\n{exc}'
