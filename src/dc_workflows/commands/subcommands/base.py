from abc import ABC, abstractclassmethod

class BaseSubcommand(ABC):
    """
    Parent class for any subcommand class
    """
    def __init__(self, workflow):
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
            print('profile and environment are required')

        args.profile = args.profile or args.environment

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
            self.print_subcommand_help(__doc__, error=f'unknown action={action}')


    def print_subcommand_help(self, doc, error=None):
        print(doc.lstrip())

        self.workflow.parser.print_help()

        if error:
            return f'\nError: {error}'

    def run(self):
        self._check_args()

        return self.handle()

    @classmethod
    def setup_subparser(cls, parser, subparsers):
        name = cls.__name__.lower()
        aliases = getattr(cls, 'aliases', [])

        subparser = subparsers.add_parser(name, aliases=aliases)
        subparser.set_defaults(subcommand_cls=cls)

        cls.fill_subparser(parser, subparser)
