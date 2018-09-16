"""
Compose Flow - Codified workflows for Docker Compose and Swarm

This utility is built on top of Docker Compose and Swarm Mode. It establishes
conventions for publishing Images, deploying Stacks across multiple
installations (like separate dev and prod Swarms), and working with service
containers that are easily shared between team members -- and bots -- who need
to manage running services.
"""
import argparse
import logging.config
import os
import pkg_resources  # part of setuptools
import sys

from functools import lru_cache

from .subcommands import find_subcommands, set_default_subparser
from .subcommands.env import Env
from .subcommands.profile import Profile
from .subcommands.remote import Remote

from .. import errors, settings
from ..config import DC_CONFIG_ROOT
from ..errors import CommandError, ErrorMessage
from ..utils import get_repo_name, yaml_load

PACKAGE_NAME = __name__.split('.', 1)[0].replace('_', '-')
PROJECT_NAME = get_repo_name()

CF_REMOTES_CONFIG_FILENAME = 'config.yml'
CF_REMOTES_CONFIG_PATH = os.path.expanduser(f'~/.compose/{CF_REMOTES_CONFIG_FILENAME}')


class Workflow(object):
    def __init__(self, argv=None):
        self.argv = argv or sys.argv[1:]

        self.parser = self.get_argument_parser()
        self.args, self.args_remainder = self.parser.parse_known_args(self.argv)

        self._set_arg_defaults()

        # the subcommand that is being run; defined in run() below
        self.subcommand = None

        if os.path.exists(DC_CONFIG_ROOT):
            os.chdir(DC_CONFIG_ROOT)

    @property
    def app_config(self) -> dict:
        """
        Returns the application config
        """
        app_config = {}

        config_path = os.environ.get('CF_REMOTES_CONFIG_PATH', CF_REMOTES_CONFIG_PATH)
        if os.path.exists(config_path):
            with open(config_path, 'r') as fh:
                app_config = yaml_load(fh)

        return app_config

    def _check_version_option(self):
        version_arg = self.args.version
        if version_arg:
            version = pkg_resources.require(PACKAGE_NAME)[0].version

            print(f'{version}')

        return version_arg

    @property
    def config_name(self):
        return self.args.config_name or self.project_name

    @property
    @lru_cache()
    def environment(self):
        """
        Returns an Env instance
        """
        environment = Env(self)

        if self.subcommand.rw_env:
            environment.update_workflow_env()

        return environment

    def get_argument_parser(self, doc: str=None):
        argparse.ArgumentParser.set_default_subparser = set_default_subparser

        doc = doc or __doc__

        parser = argparse.ArgumentParser(
            epilog=doc,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # defaults for these args are set in _set_arg_defaults() below
        parser.add_argument('-c', '--config-name')
        parser.add_argument('-e', '--environment')
        parser.add_argument('-p', '--profile')
        parser.add_argument(
            '-n', '--project-name',
            help=f'the project name to use, default={PROJECT_NAME}'
        )
        parser.add_argument(
            '-r', '--remote',
            help=f'the label of the remote system to connect to, default same name as the environment'
        )

        # misc args
        parser.add_argument(
            '--dirty',
            action='store_true',
            help='allow dirty working copy for this command'
        )
        parser.add_argument('-l', '--loglevel', default='INFO')
        parser.add_argument(
            '--noop', '--dry-run',
            action='store_true', dest='dry_run',
            help='just print command, do not execute'
        )
        parser.add_argument('--version', action='store_true', help='print version and exit')

        self.subparsers = parser.add_subparsers(dest='command')

        for subcommand in find_subcommands():
            subcommand.setup_subparser(parser, self.subparsers)

        parser.set_default_subparser('help')

        return parser

    @property
    @lru_cache()
    def profile(self):
        return Profile(self)

    def _render_profile(self):
        """
        Writes a compiled compose file using the info in the yml file
        """
        self.profile.write()

    def run(self):
        # setup the loglevel
        logging_config = settings.LOGGING
        logging_config['loggers']['compose_flow']['level'] = self.args.loglevel.upper()
        logging.config.dictConfig(logging_config)

        if self._check_version_option():
            return

        try:
            self._setup_remote()

            self._render_profile()

            # execute the subcommand
            self.subcommand.handle()

            self._write_environment()
        except CommandError as exc:
            self.parser.print_help()

            return f'\n{exc}'
        except ErrorMessage as exc:
            return f'\n{exc}'

    def _set_arg_defaults(self):
        """
        Sets the default arguments relative to the set variables

        NOTE: an environment can be None!
        """
        if self.args.project_name is None:
            self.args.project_name = PROJECT_NAME

        # when no profile or remote is given, they take on the same as the environment name
        if self.args.profile is None:
            self.args.profile = self.args.environment

        if self.args.remote is None:
            self.args.remote = self.args.environment

        # the config name is generated from the environment and project name
        if self.args.config_name is None:
            prefix = ''
            if self.args.environment:
                prefix = f'{self.args.environment}-'

            self.args.config_name = f'{prefix}{self.args.project_name}'

    def _setup_remote(self):
        """
        Sets DOCKER_HOST based on the environment
        """
        remote = Remote(self)

        try:
            remote.make_connection(use_existing=True)
        except (errors.AlreadyConnected, errors.RemoteUndefined):
            pass
        except errors.NotConnected as exc:
            if not self.is_not_connected_okay(exc):
                raise

        docker_host = remote.docker_host
        if docker_host:
            os.environ.update({
                'DOCKER_HOST': docker_host,
            })

    @property
    @lru_cache()
    def subcommand(self):
        return self.args.subcommand_cls(self)

    @subcommand.setter
    def subcommand(self, value):
        """
        This can only be used to clear the subcommand
        """
        assert value == None

        self.__class__.subcommand.fget.cache_clear()

    def _write_environment(self):
        """
        Writes environment back out to the docker config
        """
