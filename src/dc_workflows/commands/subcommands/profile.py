"""
Profile subcommand
"""
from .base import BaseSubcommand


class Profile(BaseSubcommand):
    """
    Subcommand for managing profiles
    """
    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action')

    def handle(self):
        print(self.workflow.args)
