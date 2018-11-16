class BaseBackend:
    def list_configs(self):
        raise NotImplementedError()

    def read(self, name: str):
        raise NotImplementedError()

    def write(self, name: str, path: str):
        """
        Writes the environment to the backend

        Args:
            name: the environment name
            path: the path to the config on disk
        """
        raise NotImplementedError()
