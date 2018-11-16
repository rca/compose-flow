import os

from compose_flow.settings import APP_ENVIRONMENTS_ROOT

from .base_backend import BaseBackend


class LocalBackend(BaseBackend):
    """
    Manages local file storage
    """
    def __init__(self, *args, root: str, **kwargs):
        """
        Constructor

        Args:
            root: the base directory where to look for local environment files
        """
        super().__init__(*args, **kwargs)

        self.root = root

    def list_configs(self):
        return os.listdir(self.root)

    def read(self, name: str):
        """
        Reads in the environment file
        """
        with open(os.path.join(APP_ENVIRONMENTS_ROOT, name), 'r') as fh:
            return fh.read()

    def write(self, name: str, path: str):
        # create the directory if it does not exist
        if not os.path.exists(APP_ENVIRONMENTS_ROOT):
            os.makedirs(APP_ENVIRONMENTS_ROOT)

        with open(path, 'r') as fh:
            buf = fh.read()

        with open(os.path.join(APP_ENVIRONMENTS_ROOT, name), 'w') as fh:
            fh.write(buf)
