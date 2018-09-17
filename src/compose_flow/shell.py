import sh
import shlex

from sh import ErrorReturnCode_1


def execute(command: str, env, **kwargs):
    """
    Executes a shell command
    """
    command_split = shlex.split(command)

    kwargs.update(dict(_env=env))

    proc = getattr(sh, command_split[0])

    return proc(*command_split[1:], **kwargs)
