from unittest import TestCase, mock

from compose_flow import shell


@mock.patch('compose_flow.shell.sh')
class ShellTestCase(TestCase):
    def test_execute(self, *mocks):
        """
        Ensure the shell's execution is done with the passed in environment
        """
        env = mock.Mock()

        shell.execute('docker ps', env)

        sh_mock = mocks[-1]
        sh_mock.docker.assert_called_with('ps', _env=env)
