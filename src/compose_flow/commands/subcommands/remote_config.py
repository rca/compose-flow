"""
Remote configuration subcommand
"""
import os
import tempfile

import yaml

from .config_base import ConfigBaseSubcommand

from compose_flow import docker
from compose_flow.errors import NoSuchConfig


class RemoteConfig(ConfigBaseSubcommand):
    """
    Subcommand for managing remote configuration
    """
    def __init__(self, *args, **kwargs):
        self.config_name = kwargs.pop('config_name', 'compose-flow-remotes')

        super().__init__(*args, **kwargs)

    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action')

    def cat(self):
        """
        Prints the loaded compose file to stdout
        """
        print(self.load())

    def is_missing_config_okay(self, exc):
        return True

    def is_missing_env_arg_okay(self):
        return True

    def is_missing_profile_okay(self, exc):
        return True

    def load(self) -> str:
        """
        Loads the compose file that is generated from all the items listed in the profile
        """
        try:
            config = docker.get_config(self.config_name)
        except NoSuchConfig as exc:
            return f'{exc.__class__.__name__}: Missing remote config {self.config_name}'

        return config

    def render_buf(self, fh):
        fh.write(self.load())
