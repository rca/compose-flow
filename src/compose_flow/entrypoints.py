"""
Entrypoints module

Main console script entrypoints for the dc tool
"""
import logging
import sys

from .commands import ComposeFlow


def compose_flow():
    """
    Main entrypoint
    """
    logging.basicConfig(level=logging.WARN)

    sys.exit(ComposeFlow().run())
