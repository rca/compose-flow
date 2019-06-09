import sys
import sh

from .base_backend import BaseBackend

from compose_flow import docker


class SwarmBackend(BaseBackend):
    """
    Manages `docker config` storage
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # put this on hold for now.  in order to get this working on jenkins agents that
        # are not swarm managers.  this test should probably occur somewhere closer to when
        # a config is being pulled out of a local docker instance
        # self._check_swarm()

    def _check_swarm(self):
        """
        Checks to see if Docker is setup as a swarm
        """
        try:
            self.execute('docker config ls')  # pylint: disable=E1101
        except sh.ErrorReturnCode_1 as exc:  # pylint: disable=E1101
            message = exc.stderr.decode('utf8').strip().lower()

            if 'this node is not a swarm manager' in message:
                self.init_swarm(prompt=True)
            else:
                raise

    def init_swarm(self, prompt: bool = False) -> None:
        """
        Prompts to initialize a local swarm
        """
        try:
            self.execute('docker config ls')  # pylint: disable=E1101
        except:
            pass
        else:
            return

        environment = self.workflow.environment  # pylint: disable=E1101

        docker_host = environment.data.get('DOCKER_HOST')
        if docker_host:
            docker_host_message = f'docker host at {docker_host}'
        else:
            docker_host_message = 'docker host'

        message = (
            f'It looks like your {docker_host_message} is not setup for a swarm.'
            '\nSwarm is needed in order to store configuration directly on Docker itself.'
            '\n\nWould you like to configure it now? [N|y]: '
        )

        init_swarm = True
        if prompt:
            print(message, end='')
            response = sys.stdin.readline().strip()

            response = response.upper() or 'N'
            if response != 'Y':
                init_swarm = False

        if init_swarm:
            self.execute('docker swarm init')  # pylint: disable=E1101

    def ls(self) -> list:
        return docker.get_configs()

    def read(self, name: str) -> str:
        return docker.get_config(name)

    def rm(self, name: str) -> None:
        """
        Removes a config from Swarm
        """
        docker.remove_config(name)

    def write(self, name: str, path) -> None:
        """
        Saves an environment into the swarm
        """
        docker.load_config(name, path)
