"""
Env subcommand
"""
from .base import BaseSubcommand

from dc_workflows import docker


class Env(BaseSubcommand):
    """
    Subcommand for managing profiles
    """
    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action')
        subparser.add_argument('path', nargs='*')

    def cat(self):
        if self.env_name not in docker.get_configs():
            return f'docker config named {self.env_name} not in swarm'

        print(docker.get_config(self.env_name))

    @property
    def data(self):
        data = {}

        env = docker.get_config(self.env_name)
        for line in env.splitlines():
            # skip empty lines
            if line.strip() == '':
                continue

            # skip commented lines
            if line.startswith('#'):
                continue

            try:
                key, value = line.split('=', 1)
            except ValueError as exc:
                print(f'unable to split line={line}')
                raise

            data[key] = value

        return data

    def load(self):
        """
        Loads an environment into the swarm
        """
        path = self.args.path
        if not path:
            return self.print_subcommand_help(__doc__, error='path needed to load')

        docker.load_config(self.env_name, self.args.path)

    def rm(self):
        """
        Removes an environment from the swarm
        """
        docker.remove_config(self.env_name)
