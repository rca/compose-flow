"""
Env subcommand
"""
import io
import logging
import sys
import tempfile

import sh

from .base import BaseSubcommand

from compose_flow import docker, errors


class Env(BaseSubcommand):
    """
    Subcommand for managing environment
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

        self._config = None

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

        print(self.render())

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

    def is_dirty_working_copy_okay(self, exc):
        return self.workflow.args.action in ('cat', 'push')

    def is_env_error_okay(self, exc):
        return self.workflow.args.action in ('push',)

    def is_write_profile_error_okay(self, exc):
        return self.workflow.args.action in ('push',)

    def load(self) -> str:
        """
        Loads an environment from the docker swarm config
        """
        if self._config:
            return self._config

        self._config = docker.get_config(self.env_name)

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
                # check if the subcommand is okay with a dirty working copy
                if not self.workflow.subcommand.is_dirty_working_copy_okay(exc):
                    raise errors.TagVersionError(f'Warning: unable to run tag-version ({exc})\n')

        # check if adding a newline to the end of the file is necessary
        new_line = '\n'
        if self._config.endswith('\n'):
            new_line = ''

        version_var = 'VERSION'
        if version_var not in self.data:
            self._config += f'{new_line}{version_var}={tag_version}\n'

        return self._config

    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def push(self, path:str=None) -> None:
        """
        Saves an environment into the swarm
        """
        path = path or self.args.path
        if not path:
            return self.print_subcommand_help(__doc__, error='path needed to load')

        docker.load_config(self.env_name, path)

    def render(self, data:dict=None) -> str:
        """
        Returns a rendered file in .env file format
        """
        buf = io.StringIO()

        data = data or self.data
        for k, v in data.items():
            buf.write(f'{k}={v}\n')

        return buf.getvalue()

    def rm(self) -> None:
        """
        Removes an environment from the swarm
        """
        docker.remove_config(self.env_name)

    def write_tag(self) -> None:
        """
        Writes the projects tag version into the environment

        This currently writes the tag to the `DOCKER_IMAGE` variable
        """
        data = self.data

        image_base = data['DOCKER_IMAGE'].rsplit(':', 1)[0]
        data['DOCKER_IMAGE'] = f'{image_base}:{data["VERSION"]}'

        with tempfile.NamedTemporaryFile('w+') as fh:
            fh.write(self.render(data))
            fh.flush()

            fh.seek(0, 0)

            self.push(path=fh.name)
