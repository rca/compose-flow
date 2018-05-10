import argparse
import sys

from .subcommands import find_subcommands


class DCWorkflow(object):
    def __init__(self, argv=None):
        self.argv = argv or sys.argv

        parser = self.get_argument_parser(self.argv)

        self.args = parser.parse_args()

    def get_argument_parser(self, argv):
        parser = argparse.ArgumentParser(argv)

        parser.add_argument('-e', '--environment')
        parser.add_argument('-p', '--profile')
        parser.add_argument(
            '-n', '--noop', '--dry-run',
            action='store_true', dest='dry_run',
            help='just print command, do not execute'
        )

        for subcommand in find_subcommands():
            print(f'subcommand={subcommand}')

        return parser

    def run(self):
        print(f'DCWorkflow.run(), args={self.args}')
