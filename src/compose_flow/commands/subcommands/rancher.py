"""
Compose subcommand
"""
from .passthrough_base import PassthroughBaseSubcommand
import yaml
import sh
import os
from compose_flow.config import get_config
from compose_flow import shell
from .rancher_mixin import RancherMixIn


class Rancher(PassthroughBaseSubcommand, RancherMixIn):
    """
    Subcommand for running rancher CLI commands
    """

    command_name = 'rancher'

    setup_environment = True

    setup_profile = False

    def handle(self, extra_args: list = None) -> [None, str]:
        self.switch_context()

        return super().handle(log_output=True)
