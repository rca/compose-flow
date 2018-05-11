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

    def cat(self):
        print(f'{self.__class__.__name__} cat!')

    def handle(self):
        return self.handle_action()
