from unittest import TestCase, mock

from compose_flow import shell

from tests import BaseTestCase


class ShellTestCase(BaseTestCase):
    def test_execute(self, *mocks):
        """
        Ensure the shell's execution is done with the passed in environment
        """
        env = mock.Mock()

        shell.execute('docker ps', env)

        self.sh_mock.docker.assert_called_with('ps', _env=env)
