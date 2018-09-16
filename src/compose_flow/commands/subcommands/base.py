import logging
import os

from abc import ABC, abstractclassmethod

from compose_flow import errors
from compose_flow.config import get_config
from compose_flow.errors import CommandError, EnvError, NoSuchConfig, \
    NoSuchProfile, NotConnected, ProfileError, TagVersionError


class BaseSubcommand(ABC):
    """
    Parent class for any subcommand class
    """
    dirty_working_copy_okay = False

    # whether this subcommand should connect to the remote host
    remote_action = True

    # whether the env should be in read/write mode
    rw_env = False

    def __init__(self, workflow):
        self.workflow = workflow

    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def get_subcommand(self, name:str) -> object:
        """
        Returns the requested subcommand class by name
        """
        from . import get_subcommand_class

        subcommand_cls = get_subcommand_class(name)

        return subcommand_cls(self.workflow)

    @abstractclassmethod
    def fill_subparser(cls, parser, subparser):
        """
        Stub for adding arguments to this subcommand's subparser
        """

    def handle(self):
        return self.handle_action()

    def handle_action(self):
        action = self.workflow.args.action

        action_fn = getattr(self, f'action_{action}', None)
        if not action_fn:
            action_fn = getattr(self, action, None)

        if action_fn:
            return action_fn()
        else:
            self.print_subcommand_help(self.__doc__, error=f'unknown action={action}')

    def is_dirty_working_copy_okay(self, exc: Exception) -> bool:
        """
        Checks to see if the project's compose-flow.yml allows for the env to use a dirty working copy

        To configure an environment to allow a dirty working copy, add the following to the compose-flow.yml

        ```
        options:
          env_name:
            dirty_working_copy_okay: true
        ```

        This defaults to False
        """
        config = get_config() or {}
        env = self.workflow.args.environment

        dirty_working_copy_okay = self.workflow.args.dirty or config.get('options', {}).get(env, {}).get(
            'dirty_working_copy_okay', self.dirty_working_copy_okay
        )

        return dirty_working_copy_okay

    def is_env_error_okay(self, exc):
        return False

    def is_env_runtime_error_okay(self):
        return False

    def is_missing_config_okay(self, exc):
        return False

    def is_missing_env_arg_okay(self):
        return False

    def is_missing_profile_okay(self, exc):
        return False

    def is_not_connected_okay(self, exc):
        return False

    def is_write_profile_error_okay(self, exc):
        return False

    def print_subcommand_help(self, doc, error=None):
        print(doc.lstrip())

        self.workflow.parser.print_help()

        if error:
            return f'\nError: {error}'

    def run(self, *args, **kwargs):
        return self.handle(*args, **kwargs)

    @classmethod
    def setup_subparser(cls, parser, subparsers):
        name = cls.__name__.lower()
        aliases = getattr(cls, 'aliases', [])

        subparser = subparsers.add_parser(name, aliases=aliases)
        subparser.set_defaults(subcommand_cls=cls)

        cls.fill_subparser(parser, subparser)

    def update_runtime_environment(self, **kwargs):
        """
        Updates os.environ with the current environment
        """
        try:
            runtime_env = self.workflow.environment.data
        except NoSuchConfig as exc:
            if not self.workflow.subcommand.is_env_error_okay(exc):
                raise
        else:
            os.environ.update(runtime_env)
