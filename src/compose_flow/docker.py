import base64
import json
import os

from compose_flow import shell

from .errors import DockerError, NoSuchConfig, NotConnected


def get_configs() -> list:
    """
    Returns a list of config names found in the swarm
    """
    output = get_docker_output('docker config ls --format "{{ .Name }}"', os.environ)

    return output.splitlines()


def get_config(name: str) -> str:
    """
    Returns the content of the config in the swarm
    """
    try:
        data = get_docker_json(f'docker config inspect {name}', os.environ)
    except DockerError as exc:
        exc_s = str(exc)

        # if the config does not exist in docker, raise NoSuchConfig
        if 'no such config' in exc_s:
            raise NoSuchConfig(f'config name={name} not found')

        raise

    config_data = data[0]['Spec']['Data']

    return base64.b64decode(config_data).decode('utf8')


def load_config(name: str, path: str) -> None:
    """
    Loads config into swarm
    """
    configs = get_configs()
    if name in configs:
        remove_config(name)

    shell.execute(f'docker config create {name} {path}', os.environ)


def remove_config(name: str) -> None:
    """
    Removes a config from the swarm
    """
    shell.execute(f'docker config rm {name}', os.environ)


def get_docker_json(command: str, env: dict) -> dict:
    """
    Returns docker output as a JSON object

    Args:
        command: the docker command to run
        env: the environment to run the command with

    Returns:
        dict
    """
    content = get_docker_output(command, env)

    return json.loads(content)


def get_docker_output(command: str, env: dict) -> str:
    """
    Returns docker stdout as a string

    Args:
        command: the docker command to run
        env: the environment to run the command under

    Returns:
        str
    """
    try:
        proc = shell.execute(command, env)
    except shell.ErrorReturnCode_1 as exc:
        exc_s = f'{exc}'.lower()
        if 'cannot connect to the docker daemon' in exc_s:
            raise NotConnected()

        raise DockerError(exc)

    return proc.stdout.decode('utf8')
