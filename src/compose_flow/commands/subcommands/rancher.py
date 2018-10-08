"""
Rancher CLI subcommand
"""
from .passthrough_base import PassthroughBaseSubcommand
from .kube_mixin import KubeMixIn


class Rancher(PassthroughBaseSubcommand, KubeMixIn):
    """
    Subcommand for running rancher CLI commands
    """

    command_name = 'rancher'

    setup_environment = True

    setup_profile = False

    def handle(self, extra_args: list = None) -> [None, str]:
        self.switch_context()

        return super().handle(log_output=True)
