from abc import ABC, abstractclassmethod

from compose_flow.errors import CommandError, EnvError, NotConnected, ProfileError, TagVersionError

class BaseSubcommand(ABC):
    """
    Parent class for any subcommand class
    """
    dirty_working_copy_okay = False

    def __init__(self, workflow):
        self.profile = None  # populated in run()
        self.workflow = workflow

    @property
    def args(self):
        return self.workflow.args

    def _check_args(self):
        """
        Checks and transforms the command line arguments
        """
        args = self.workflow.args

        if None in (args.environment,):
            raise CommandError('Error: environment is required')

        args.profile = args.profile or args.environment

    def get_subcommand(self, name:str) -> object:
        """
        Returns the requested subcommand class by name
        """
        from . import get_subcommand_class

        subcommand_cls = get_subcommand_class(name)

        return subcommand_cls(self.workflow)

    @property
    def env(self):
        """
        Returns an Env instance
        """
        # avoid circular import
        from .env import Env

        return Env(self.workflow)

    @property
    def env_name(self):
        args = self.workflow.args

        return f'{args.environment}-{args.project_name}'

    @abstractclassmethod
    def fill_subparser(cls, parser, subparser):
        """
        Stub for adding arguments to this subcommand's subparser
        """

    def handle(self):
        return self.handle_action()

    def handle_action(self):
        action = self.workflow.args.action

        action_fn = getattr(self, action, None)
        if action_fn:
            return action_fn()
        else:
            self.print_subcommand_help(self.__doc__, error=f'unknown action={action}')

    def is_dirty_working_copy_okay(self, exc):
        return self.dirty_working_copy_okay

    def is_env_error_okay(self, exc):
        return False

    def is_missing_profile_okay(self, exc):
        return False

    def is_write_profile_error_okay(self, exc):
        return False

    def print_subcommand_help(self, doc, error=None):
        print(doc.lstrip())

        self.workflow.parser.print_help()

        if error:
            return f'\nError: {error}'

    def run(self, *args, **kwargs):
        self._check_args()

        try:
            self._write_profile()
        except (EnvError, NotConnected, ProfileError, TagVersionError) as exc:
            if not self.is_write_profile_error_okay(exc):
                raise

        return self.handle(*args, **kwargs)

    @classmethod
    def setup_subparser(cls, parser, subparsers):
        name = cls.__name__.lower()
        aliases = getattr(cls, 'aliases', [])

        subparser = subparsers.add_parser(name, aliases=aliases)
        subparser.set_defaults(subcommand_cls=cls)

        cls.fill_subparser(parser, subparser)

    def _write_profile(self):
        from .profile import Profile

        self.profile = Profile(self.workflow)
        self.profile.write()
