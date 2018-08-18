"""
Env subcommand
"""
import io
import logging
import os
import shlex
import sys
import tempfile

from functools import lru_cache

import sh

from .config_base import ConfigBaseSubcommand

from compose_flow import docker, errors, utils

VERSION_VAR = 'VERSION'


class Env(ConfigBaseSubcommand):
    """
    Subcommand for managing environment
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

        self._config = None

    @property
    def config_name(self):
        return self.workflow.args.config_name or self.project_name

    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action')
        subparser.add_argument('path', nargs='*')
        subparser.add_argument('-f', '--force', action='store_true', help='edit even if no config found')
        subparser.add_argument('--variables', action='store_true', help='show runtime variables instead of values')

    def cat(self) -> str:
        """
        Prints the loaded config to stdout
        """
        config_name = self.config_name

        if config_name not in docker.get_configs():
            return f'docker config named {config_name} not in swarm'

        print(self.render())

    @property
    def data(self) -> dict:
        return self.get_data()

    @lru_cache()
    def get_data(self, load_cf_env: bool=None) -> dict:
        """
        Returns the loaded config as a dictionary

        Args:
            load_cf_env: whether to include the current action's env.  if False, only
                basic variables are set
        """
        data = {
            'DOCKER_IMAGE': self.docker_image,
            VERSION_VAR: self.version,
        }

        load_cf_env = load_cf_env or self.workflow.subcommand.load_cf_env
        if not load_cf_env:
            return data

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

        subcommand = self.workflow.subcommand
        if subcommand.rw_env:
            data['DOCKER_IMAGE'] = f'{self.docker_image.split(":", 1)[0]}:{self.version}'

        # deprecate this env var
        data['CF_ENV_NAME'] = self.project_name

        data['CF_ENV'] = self.env_name
        data['CF_PROJECT'] = self.project_name

        # render placeholders
        for k, v in data.items():
            if not v.startswith('runtime://'):
                continue

            location, location_ref = v.split('://', 1)
            location_ref = location_ref or k

            if k not in self._rendered_config:
                self._rendered_config[k] = v

            new_val = os.environ.get(location_ref)
            if new_val is None:
                raise errors.RuntimeEnvError(f'runtime substitution for {k}={v} not found')

            data[k] = new_val

        # render substitutions
        sub_count = True
        while sub_count:
            # reset the substitution count to break the loop when no subs are made
            sub_count = 0

            for k, v in data.items():
                rendered = utils.render(v, env=data)

                if rendered != v:
                    sub_count += 1

                    if k not in self._rendered_config:
                        self._rendered_config[k] = v

                    data[k] = rendered

        return data

    @property
    def docker_image(self) -> str:
        """
        Generates a docker image name for this action
        """
        registry_domain = os.environ['CF_DOCKER_IMAGE_PREFIX']
        project_name = self.workflow.args.project_name
        env = self.workflow.args.environment

        docker_image = f'{registry_domain}/{project_name}:{env}'

        return self.set_docker_tag(docker_image)

    def set_docker_tag(self, docker_image: str) -> str:
        """
        Sets the docker image tag based on the current version
        """
        if ':' not in docker_image:
            raise EnvironmentError('compose-flow enforces image versioning; DOCKER_IMAGE must contain a colon')

        return f'{docker_image.split(":", 1)[0]}:{self.version}'

        return docker_image

    def is_dirty_working_copy_okay(self, exc: Exception) -> bool:
        is_dirty_working_copy_okay = super().is_dirty_working_copy_okay(exc)

        return is_dirty_working_copy_okay or self.is_env_modification_action()

    def is_env_error_okay(self, exc):
        return self.workflow.args.action in ('push',)

    def is_env_runtime_error_okay(self):
        return self.is_env_modification_action()

    def is_missing_config_okay(self, exc):
        subcommand = self.workflow.subcommand
        # the `force` attribute may not exist
        force = 'force' in subcommand.args and subcommand.args.force

        try:
            action = self.workflow.args.action
        except AttributeError:
            action = None

        return action in ('edit',) and force

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
            self._config = docker.get_config(self.config_name)
        except errors.NoSuchConfig as exc:
            if not self.is_missing_config_okay(exc):
                raise

            self._config = ''

        data = self.data

        subcommand = self.workflow.subcommand
        if subcommand.rw_env or VERSION_VAR not in data:
            data[VERSION_VAR] = self.version

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

        try:
            runtime_config = not self.args.variables
        except AttributeError:
            runtime_config = True

        self.render_buf(buf, data=data, runtime_config=runtime_config)

        return buf.getvalue()

    def rm(self) -> None:
        """
        Removes an environment from the swarm
        """
        docker.remove_config(self.project_name)

    @property
    @lru_cache()
    def version(self):
        """
        Returns a version string for the current version of code
        """
        # default the tag version to the name of the environment
        tag_version = self.workflow.args.environment
        try:
            tag_version = utils.get_tag_version()
        except Exception as exc:
            subcommand = self.workflow.subcommand

            # check if the subcommand is okay with a dirty working copy
            if not subcommand.is_dirty_working_copy_okay(exc):
                raise errors.TagVersionError(f'Warning: unable to run tag-version ({exc})\n')

        return tag_version

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
