import os
import sh
import shlex

from sh import ErrorReturnCode_1

# these runtime environment variables should be injected into
# the compose flow environment prior to executing a command
OS_ENV_INCLUDES = ('DOCKER_HOST', 'HOME', 'PATH')


def execute(command: str, env, **kwargs):
    """
    Executes a shell command
    """
    command_split = shlex.split(command)

    # make a copy of the environment and inject the DOCKER_HOST
    _env = env.copy()

    for env_var in OS_ENV_INCLUDES:
        env_val = os.environ.get(env_var)
        if env_val:
            _env.update({env_var: env_val})

    kwargs.update(dict(_env=_env))

    proc = getattr(sh, command_split[0])

    return proc(*command_split[1:], **kwargs)
