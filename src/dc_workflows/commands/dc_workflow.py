import argparse
import sys

from .subcommands import find_subcommands, set_default_subparser


class DCWorkflow(object):
    def __init__(self, argv=None):
        self.argv = argv or sys.argv

        self.parser = self.get_argument_parser(self.argv)

        self.args = self.parser.parse_args()

    def get_argument_parser(self, argv):
        argparse.ArgumentParser.set_default_subparser = set_default_subparser

        parser = argparse.ArgumentParser(argv)

        parser.add_argument('-e', '--environment')
        parser.add_argument('-p', '--profile')
        parser.add_argument(
            '-n', '--noop', '--dry-run',
            action='store_true', dest='dry_run',
            help='just print command, do not execute'
        )

        self.subparsers = parser.add_subparsers(dest='command')

        for subcommand in find_subcommands():
            subcommand.setup_subparser(parser, self.subparsers)

        parser.set_default_subparser('help')

        return parser

    def run(self):
        subcommand = self.args.subcommand_cls(self)

        subcommand.run()
