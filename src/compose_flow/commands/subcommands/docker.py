"""
Compose subcommand
"""
from .passthrough_base import PassthroughBaseSubcommand


class Docker(PassthroughBaseSubcommand):
    """
    Subcommand for running docker commands
    """

    command_name = 'docker'
