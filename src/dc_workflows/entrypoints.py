"""
Entrypoints module

Main console script entrypoints for the dc tool
"""
import sys

from .commands import DCWorkflow


def dc():
    """
    Main entrypoint
    """
    sys.exit(DCWorkflow().run())
