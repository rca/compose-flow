"""
Env subcommand
"""
import io
import logging
import os
import shlex
import sys
import tempfile

import sh

from .config_base import ConfigBaseSubcommand

from compose_flow import docker, errors


class Env(ConfigBaseSubcommand):
    """
    Subcommand for managing environment
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

        self._config = None

    @property
    def config_name(self):
        return self.env_name

    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action')
        subparser.add_argument('path', nargs='*')
        subparser.add_argument('-f', '--force', action='store_true', help='edit even if no config found')

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

        # TODO: this is hacky because of the back-and-forth relationship
        # between data() and load() ... gotta fix this.
        docker_image = data.get('DOCKER_IMAGE')
        if 'VERSION' in data and docker_image and ':' in docker_image:
            data['DOCKER_IMAGE'] = f'{docker_image.split(":", 1)[0]}:{data["VERSION"]}'

        data['CF_ENV_NAME'] = self.env_name

        return data

    def is_dirty_working_copy_okay(self, exc):
        return self.is_env_modification_action()

    def is_env_error_okay(self, exc):
        return self.workflow.args.action in ('push',)

    def is_missing_config_okay(self, exc):
        return self.workflow.args.action in ('edit',) and self.workflow.subcommand.args.force

    def is_env_modification_action(self):
        return self.workflow.args.action in ('cat', 'edit', 'push')

    def is_write_profile_error_okay(self, exc):
        return self.is_env_modification_action()

    def load(self) -> str:
        """
        Loads an environment from the docker swarm config
        """
        if self._config is not None:
            return self._config

        try:
            self._config = docker.get_config(self.env_name)
        except errors.NoSuchConfig as exc:
            okay = False
            try:
                if self.workflow.subcommand.args.action == 'edit' and self.workflow.subcommand.args.force:
                    okay = True
            except AttributeError:
                pass

            if not okay:
                raise

            self._config = ''

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

        data = self.data

        version_var = 'VERSION'
        data[version_var] = tag_version
        self._config = self.render(data)

        return self._config

    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def render(self, data:dict=None) -> str:
        """
        Returns a rendered file in .env file format
        """
        buf = io.StringIO()

        self.render_buf(buf, data=data)

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
