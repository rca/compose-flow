"""
Entrypoints module

Main console script entrypoints for the dc tool
"""
import logging
import sys

from .commands import DCWorkflow


def dc():
    """
    Main entrypoint
    """
    logging.basicConfig(level=logging.WARN)

    sys.exit(DCWorkflow().run())
