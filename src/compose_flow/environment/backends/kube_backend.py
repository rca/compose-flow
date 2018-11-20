import base64
import os
import sh
import yaml

from .base_backend import BaseBackend

from compose_flow.kube.mixins import KubeMixIn
from compose_flow.errors import MissingKubeContextError, NoSuchConfig
from compose_flow import shell


class KubeBackend(BaseBackend, KubeMixIn):
    """
    Manages native `kubectl secret` storage
    """
    env_key = '_env'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.secret_exists = None
        self.workflow = kwargs.get('workflow')

        self.switch_kube_context()
        self._check_context()
        self._check_namespace()

    @property
    def namespace(self):
        return f'{self.workflow.args.profile}-compose-flow'

    @property
    def secret_name(self):
        return f'{self.workflow.config_name}'

    def execute(self, command: str, **kwargs):
        env = os.environ
        return shell.execute(command, env, **kwargs)

    def _check_context(self):
        """
        Checks to see if there is a kubecontext configured
        """
        try:
            self.execute('kubectl config current-context')
        except sh.ErrorReturnCode_1 as exc:
            message = exc.stderr.decode('utf8').strip().lower()

            if 'current-context is not set' in message:
                raise MissingKubeContextError('No current context configured in kubectl!')

    def _check_namespace(self):
        """
        Checks for existence of the target namespace.

        If not found, attempt to create it.
        """
        try:
            self.execute(f'kubectl get namespace {self.namespace}')
        except sh.ErrorReturnCode_1 as exc:
            message = exc.stderr.decode('utf8').strip().lower()

            if f'namespaces "{self.namespace}" not found' in message:
                self.logger.warning("Namespace '%s' not found - attempting to create it...", self.namespace)
                self.execute(f'kubectl create namespace {self.namespace}')

    def ls(self) -> list:
        """List kubectl secrets in the proper namespace"""
        return self.execute(f'kubectl get secrets --namespace {self.namespace}')

    def read(self, name: str) -> str:
        try:
            raw_secret = self.execute(
                f'kubectl get secrets --namespace {self.namespace} -o yaml {self.secret_name}'
            )
            self.secret_exists = True
        except sh.ErrorReturnCode_1 as exc:
            message = exc.stderr.decode('utf8').strip().lower()

            if f'secrets "{self.secret_name}" not found' in message:
                self.secret_exists = False
                raise NoSuchConfig(f'secret name={self.secret_name} not found')

            raise

        secret_yaml = yaml.load(raw_secret.stdout)
        payload = secret_yaml.get('data')
        if not payload or '_env' not in payload:
            raise NoSuchConfig("secret name={self.secret_name} is empty")

        return base64.b64decode(secret_yaml['data']['_env']).decode('utf8')

    def write(self, name: str, path) -> None:
        """
        Saves an environment into a Secret
        """
        with open(path, 'r') as stream:
            b64_env = base64.b64encode(stream.read().encode()).decode('utf8')

        patch_string = f'{{"data": {{"{self.env_key}": "{b64_env}"}}}}'
        if not self.secret_exists:
            try:
                self.execute(f"kubectl create secret generic --namespace {self.namespace} {self.secret_name}")
            except sh.ErrorReturnCode_1 as exc:
                message = exc.stderr.decode('utf8').strip().lower()

                if f'secrets "{self.secret_name}" already exists' not in message:
                    raise

        self.execute(f"kubectl patch secrets --namespace {self.namespace} {self.secret_name} --patch '{patch_string}'")
