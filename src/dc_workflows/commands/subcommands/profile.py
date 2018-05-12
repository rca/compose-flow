"""
Profile subcommand
"""
from .base import BaseSubcommand

from dc_workflows.compose import get_profile_compose_file
from dc_workflows.config import get_config


class Profile(BaseSubcommand):
    """
    Subcommand for managing profiles
    """
    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action')

    def cat(self):
        config = get_config()

        profile = config['profiles'][self.args.profile]

        fh = get_profile_compose_file(profile)

        print(fh.read())

        print(f'cat profile={self.args.profile}!')

    def handle(self):
        return self.handle_action()
