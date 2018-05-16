"""
Task subcommand
"""
import shlex

from .base import BaseSubcommand

from compose_flow.config import get_config


class Task(BaseSubcommand):
    @classmethod
    def fill_subparser(self, parser, subparser):
        subparser.add_argument('name', help='the task name to process')

    def handle(self):
        config = get_config()

        task_name = self.args.name
        try:
            task = config['tasks'][task_name]
        except KeyError:
            raise CommandError('task name={task_name} not found')

        command = task['command']
        command_split = shlex.split(command)

        if command_split[0] != 'compose-flow':
            raise NotImplementedError('tasks that are not compose-flow are not yet supported')

        subcommand_name = command_split[1]
        subcommand = self.get_subcommand(subcommand_name)

        subcommand_args = command_split[2:]

        subcommand.run(subcommand_args)

        return f'{subcommand}'

    def is_dirty_working_copy_okay(self, exc):
        return self.workflow.args.environment in ('local',)
