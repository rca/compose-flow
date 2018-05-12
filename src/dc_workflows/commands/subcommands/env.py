"""
Env subcommand
"""
import sys

import sh

from .base import BaseSubcommand

from dc_workflows import docker, errors


class Env(BaseSubcommand):
    """
    Subcommand for managing environment
    """
    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action')
        subparser.add_argument('path', nargs='*')

    def cat(self) -> str:
        """
        Prints the loaded config to stdout
        """
        if self.env_name not in docker.get_configs():
            return f'docker config named {self.env_name} not in swarm'

        print(self.load())

    @property
    def data(self) -> dict:
        """
        Returns the loaded config as a dictionary
        """
        data = {}

        env = self.load()
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

    def load(self) -> str:
        """
        Loads an environment from the docker swarm config
        """
        config = docker.get_config(self.env_name)

        # inject the version from tag-version command into the loaded environment
        tag_version = 'unknown'
        try:
            tag_version_command = getattr(sh, 'tag-version')
        except Exception as exc:
            print(f'Warning: unable to find tag-version ({exc})\n', file=sys.stderr)
        else:
            try:
                tag_version = tag_version_command().stdout.decode('utf8').strip()
            except Exception as exc:
                raise errors.TagVersionError(f'Warning: unable to run tag-version ({exc})\n')


        # check if adding a newline to the end of the file is necessary
        new_line = '\n'
        if config.endswith('\n'):
            new_line = ''

        config += f'{new_line}VERSION={tag_version}\n'

        return config

    def push(self, path:str=None) -> None:
        """
        Saves an environment into the swarm
        """
        path = path or self.args.path
        if not path:
            return self.print_subcommand_help(__doc__, error='path needed to load')

        docker.load_config(self.env_name, self.args.path)

    def rm(self) -> None:
        """
        Removes an environment from the swarm
        """
        docker.remove_config(self.env_name)
