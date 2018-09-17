import os
import sh
import shlex

from sh import ErrorReturnCode_1

DOCKER_HOST_ENV_VAR = 'DOCKER_HOST'


def execute(command: str, env, **kwargs):
    """
    Executes a shell command
    """
    command_split = shlex.split(command)

    # make a copy of the environment and inject the DOCKER_HOST
    _env = env.copy()

    if DOCKER_HOST_ENV_VAR not in env:
        if DOCKER_HOST_ENV_VAR in os.environ:
            _env.update({DOCKER_HOST_ENV_VAR: os.environ.get(DOCKER_HOST_ENV_VAR)})

    kwargs.update(dict(_env=_env))

    proc = getattr(sh, command_split[0])

    return proc(*command_split[1:], **kwargs)
