"""
Helm subcommand
"""
from .passthrough_base import PassthroughBaseSubcommand


class Helm(PassthroughBaseSubcommand):
    """
    Subcommand for running rancher CLI commands
    """

    command_name = 'helm'

    setup_environment = True

    setup_profile = False
