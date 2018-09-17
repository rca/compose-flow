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

from .config_base import ConfigBaseSubcommand

from compose_flow import docker, errors, utils

VERSION_VAR = 'VERSION'


class Env(ConfigBaseSubcommand):
    """
    Subcommand for managing environment
    """
    setup_profile = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

        self._config = None
        self._docker_image = None

        self._data = {}

        # when data is modified, set this to True
        self._data_modified = False

        # keys that will be persisted to the docker config
        self._persistable_keys = []

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
        config_name = self.workflow.config_name

        if config_name not in docker.get_configs():
            return f'docker config named {config_name} not in swarm'

        print(self.render())

    @property
    def cf_env(self):
        """
        Returns defaults for the environment
        """
        args = self.workflow.args

        return {
            'CF_ENV': args.environment or '',
            'CF_PROJECT': args.project_name,
            'DOCKER_IMAGE': f'{self.docker_image.split(":", 1)[0]}:{self.version}',
            VERSION_VAR: self.version,

            # deprecate this env var
            'CF_ENV_NAME': args.project_name,
        }

    @property
    def data(self) -> dict:
        """
        Returns the loaded config as a dictionary
        """
        if self._data:
            return self._data

        data = self.load()

        args = self.workflow.args

        action = None
        if 'action' in args:
            action = args.action

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

        # set defaults when no value is set
        for k, v in self.cf_env.items():
            if k not in data:
                data[k] = v

        self._data = data

        return self._data

    @property
    def docker_image(self) -> str:
        """
        Generates a docker image name for this action
        """
        if self._docker_image:
            return self._docker_image

        registry_domain = os.environ['CF_DOCKER_IMAGE_PREFIX']
        project_name = self.workflow.args.project_name
        env = self.workflow.args.environment

        docker_image = f'{registry_domain}/{project_name}:{env}'

        self._docker_image = self.set_docker_tag(docker_image)

        return self._docker_image

    def set_docker_tag(self, docker_image: str) -> str:
        """
        Sets the docker image tag based on the current version
        """
        if ':' not in docker_image:
            raise EnvironmentError('compose-flow enforces image versioning; DOCKER_IMAGE must contain a colon')

        return f'{docker_image.split(":", 1)[0]}:{self.version}'

        return docker_image

    def update(self, new_data: dict, persistable: bool=True):
        """
        Updates the environment data with the new given data

        When persistable is True, the values being set are flagged for persisting into the docker config
        and the _data_modified flag is set
        """
        self._data.update(new_data)

        if persistable:
            self._persistable_keys.extend(list(new_data.keys()))

            self._data_modified = True

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

    def load(self) -> dict:
        """
        Loads an environment from the docker swarm config
        """
        data = {}

        # when no environment is specified on the command line, do not load any docker config
        environment = self.workflow.args.environment
        if not environment:
            return data

        try:
            content = docker.get_config(self.workflow.config_name)
        except errors.NoSuchConfig as exc:
            if not self.is_missing_config_okay(exc):
                raise

            content = ''

        for idx, line in enumerate(content.splitlines()):
            # skip empty lines
            if line.strip() == '':
                continue

            # skip commented lines
            if line.strip().startswith('#'):
                continue

            try:
                key, value = line.split('=', 1)
            except ValueError as exc:
                self.logger.error(f'ERROR: unable to parse line number {idx}, edit your env: {line}')

                raise

            data[key] = value

        # all values from the docker config are persistable
        self.update(data)

        # now that the data from the cf environment is parsed default the
        # docker image to anything that was defined in there.
        self._docker_image = data.get('DOCKER_IMAGE')

        return data

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

    def update_workflow_env(self):
        """
        Overwrites the cf environment in the data dictionary

        Even if values are already set, overwrite them with current values
        """
        self.data.update(self.cf_env)

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

    def write(self) -> None:
        """
        Writes the environment into the docker config
        """
        data = self.data

        with tempfile.NamedTemporaryFile('w+') as fh:
            fh.write(self.render(data))
            fh.flush()

            fh.seek(0, 0)

            self.push(path=fh.name)
