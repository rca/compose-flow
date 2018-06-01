import os
import shlex
import tempfile

import sh

from compose_flow import docker

from .base import BaseSubcommand


class ConfigBaseSubcommand(BaseSubcommand):
    def edit(self) -> None:
        with tempfile.NamedTemporaryFile('w') as fh:
            path = fh.name

            self.render_buf(fh)

            fh.flush()

            editor = os.environ.get('EDITOR', os.environ.get('VISUAL', 'vi'))

            command = shlex.split(f'{editor} {path}')

            # os.execve(command[0], command, os.environ)
            proc = getattr(sh, command[0])
            proc(*command[1:], _env=os.environ, _fg=True)

            self.push(path)

    def push(self, path:str=None) -> None:
        """
        Saves an environment into the swarm
        """
        path = path or self.args.path
        if not path:
            return self.print_subcommand_help(__doc__, error='path needed to load')

        docker.load_config(self.config_name, path)

    def render_buf(self, buf, data: dict=None):
        data = data or self.data
        for k, v in data.items():
            buf.write(f'{k}={v}\n')
