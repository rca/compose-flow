"""
Welcome to Docker Compose Workflows!

This is a utility around Docker Compose to make it easier to use
around commonly used workflows within your development team.
"""
from . import Subcommand


class Help(Subcommand):
    """
    Subcommand for managing profiles
    """
    @classmethod
    def fill_subparser(cls, parser, subparser):
        pass

    def run(self):
        self.print_subcommand_help(__doc__)
