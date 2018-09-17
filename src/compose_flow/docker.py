import base64
import json
import os

from compose_flow import shell

from .errors import NoSuchConfig, NotConnected


def get_configs() -> list:
    """
    Returns a list of config names found in the swarm
    """
    proc = shell.execute(f'docker config ls --format "{{ .Name }}"', os.environ)

    return proc.stdout.decode('utf8').splitlines()


def get_config(name: str) -> str:
    """
    Returns the content of the config in the swarm
    """
    try:
        proc = shell.execute(f'docker config inspect {name}', os.environ)
    except shell.ErrorReturnCode_1 as exc:
        exc_s = f'{exc}'.lower()

        # if the config does not exist in docker, raise NoSuchConfig
        if 'no such config' in exc_s:
            raise NoSuchConfig(f'config name={name} not found')
        elif 'cannot connect to the docker daemon' in exc_s:
            raise NotConnected()

        raise

    content = proc.stdout.decode('utf8')
    data = json.loads(content)

    config_data = data[0]['Spec']['Data']

    return base64.b64decode(config_data).decode('utf8')


def load_config(name: str, path: str) -> None:
    """
    Loads config into swarm
    """
    if name in get_configs():
        remove_config(name)

    shell.exeucte(f'docker config create {name} {path}')


def remove_config(name: str) -> None:
    """
    Removes a config from the swarm
    """
    shell.execute(f'docker config rm {name}')
