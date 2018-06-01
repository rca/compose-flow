"""
Connect to a remote docker swarm
"""
import os
import re
import sys

import sh

from .base import BaseSubcommand

from compose_flow.errors import EnvError, ErrorMessage

UNIX_PREFIX = 'unix://'
UNIX_REMOTE_HOST_RE = re.compile(UNIX_PREFIX + r'(?P<socket>.*)')


class Remote(BaseSubcommand):
    """
    Subcommand for connecting to a remote docker swarm
    """
    def close(self, pids=None, do_print=True):
        try:
            pids = pids or list(self.get_remote_ssh_pids())
        except EnvError:
            pass
        else:
            if do_print:
                pids_s = ", ".join([f'{x}' for x in pids])
                print(f'closing pids {pids_s}', file=sys.stderr)

            for pid in pids:
                sh.kill(pid)

        self.remove_socket()

        self.print_eval_hint()

        if do_print:
            print(f'unset DOCKER_HOST')

    def connect(self):
        try:
            pids = list(self.get_remote_ssh_pids())
        except (EnvError, ErrorMessage):
            pids = None

        try:
            remote_host = self.get_remote_host()
        except EnvError:
            remote_host = None

        try:
            if self.status(do_print=False):
                return f'already connected to {remote_host}'
        except EnvError:
            pass

        if pids:
            self.close(do_print=False)

        host = self.host
        if not host:
            raise ErrorMessage('Error: Remote host not given')

        socket_path = self.socket_path

        self.remove_socket()

        sh.ssh('-Nf', '-L', f'{socket_path}:/var/run/docker.sock', host)

        if remote_host != socket_path:
            self.print_eval_hint()

            print(f'export DOCKER_HOST={UNIX_PREFIX}{socket_path}')

    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action')
        subparser.add_argument('--host')

    def get_remote_host(self):
        return os.environ.get('DOCKER_HOST')

    def get_remote_ssh_pids(self):
        socket = self.get_socket()
        pgrep_search = f'ssh -Nf -L {socket}'

        try:
            proc = sh.pgrep('-f', pgrep_search)
        except sh.ErrorReturnCode_1:
            raise ErrorMessage('remote ssh process not found')

        for item in proc.stdout.decode('utf8').strip().splitlines():
            yield int(item)

    def get_socket(self):
        remote_host = self.get_remote_host()
        if not remote_host:
            raise EnvError('DOCKER_HOST not defined')

        matches = UNIX_REMOTE_HOST_RE.match(remote_host)
        if not matches:
            raise ErrorMessage(f'cannot parse remote_host={remote_host}')

        return matches.group('socket')

    @property
    def host(self):
        return self.args.host

    def is_env_error_okay(self, exc):
        return True

    def is_host_defined(self):
        return self.host is not None

    def is_missing_config_okay(self, exc):
        return self.is_host_defined()

    def is_missing_env_arg_okay(self):
        return self.is_host_defined()

    def is_missing_profile_okay(self, exc):
        return True

    def is_write_profile_error_okay(self, exc):
        return True

    def print_eval_hint(self):
        print(
            'copy and paste the commands below or run this command wrapped in an eval statement:\n',
            file=sys.stderr
        )

    def remove_socket(self):
        socket_path = self.socket_path
        if os.path.exists(socket_path):
            os.remove(socket_path)

    @property
    def socket_path(self):
        host = self.args.host

        return f'/tmp/compose-flow-{host}.sock'

    def status(self, do_print=True):
        pids = None
        status = False

        docker_host = self.get_remote_host()
        try:
            pids = list(self.get_remote_ssh_pids())
        except ErrorMessage:
            connected = False
        else:
            connected = True

        if docker_host and connected:
            status = True

            message = f'connected to docker_host {docker_host}, ssh pid {pids}'
        elif docker_host:
            message = f'environment set to {docker_host}, but no ssh connection found'
        elif pids:
            pids_s = ", ".join([f'{x}' for x in pids])
            message = f'ssh connection found at pids {pids_s}, but environment not setup'
        else:
            message = 'Not connected'

        if message and do_print:
            print(message)

        return status
