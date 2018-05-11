import base64
import json

import sh


def get_configs() -> list:
    """
    Returns a list of config names found in the swarm
    """
    configs = sh.docker('config', 'ls', '--format', '{{ .Name }}')

    return configs.stdout.decode('utf8').splitlines()


def get_config(name: str) -> str:
    """
    Returns the content of the config in the swarm
    """
    configs = sh.docker('config', 'inspect', name)

    content = configs.stdout.decode('utf8')
    data = json.loads(content)

    config_data = data[0]['Spec']['Data']

    return base64.b64decode(config_data).decode('utf8')


def load_config(name: str, path:str) -> None:
    """
    Loads config into swarm
    """
    if name in get_configs():
        remove_config(name)

    sh.docker('config', 'create', name, path)


def remove_config(name:str) -> None:
    """
    Removes a config from the swarm
    """
    sh.docker('config', 'rm', name)
