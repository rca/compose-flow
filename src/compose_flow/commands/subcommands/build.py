
from functools import lru_cache

from .base import BaseSubcommand


class Build(BaseSubcommand):
    """
    Subcommand for building Docker images
    """

    dirty_working_copy_okay = True
    rw_env = True
    remote_action = True
    update_version_env_vars = True

    def build(self):
        compose = self.compose

        compose.handle(extra_args=['build', '--pull'])

    @property
    @lru_cache()
    def compose(self):
        """
        Returns a Compose subcommand
        """
        from .compose import Compose

        return Compose(self.workflow)

    def handle(self):
        self.build()

    def do_validate_profile(self):
        return False

    @classmethod
    def fill_subparser(cls, parser, subparser) -> None:
        pass

    def is_missing_env_arg_okay(self):
        return True
