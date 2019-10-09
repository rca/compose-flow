import os

from .base_backend import BaseBackend

from compose_flow.kube.mixins import KubeMixIn
from compose_flow import shell


class KubeBackend(BaseBackend, KubeMixIn):
    """
    Manages native `kubectl secret` storage
    """

    kubectl_command = "kubectl"
    env_key = "_env"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.secret_exists = None
        self.workflow = kwargs.get("workflow")

        self.switch_kube_context()
        self._check_kube_context()
        self._check_kube_namespace()

    @property
    def namespace(self):
        return f"compose-flow-{self.workflow.args.profile}"

    def execute(self, command: str, **kwargs):
        env = os.environ
        return shell.execute(command, env, **kwargs)

    def ls(self) -> list:
        """List kubectl secrets in the proper namespace"""
        return self._list_secrets()

    def read(self, name: str) -> str:
        return self._read_secret_env(name)

    def rm(self, name: str) -> None:
        self._remove_secret(name)

    def write(self, name: str, path) -> None:
        """
        Saves an environment into a Secret
        """
        return self._write_secret_env(name, path)
