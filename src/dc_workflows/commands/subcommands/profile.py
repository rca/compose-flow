"""
Profile subcommand
"""
from . import Subcommand


class Profile(Subcommand):
    """
    Subcommand for managing profiles
    """
    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action')

    def handle(self):
        print(self.workflow.args)
