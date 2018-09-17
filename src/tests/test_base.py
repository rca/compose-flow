from compose_flow.commands.subcommands.base import BaseSubcommand
from tests import BaseTestCase, mock


class TestSubcommand(BaseSubcommand):
    def fill_subparser(cls, parser):
        pass


class BaseSubcommandTestCase(BaseTestCase):
    def test_execute(self, *mocks):
        print(mocks)

        workflow = mock.Mock()
        workflow.environment.data = {}

        command = TestSubcommand(workflow)
        proc = command.execute('docker ps')

        # make sure that sh was executed with the workflow environment
        sh_mock = self.sh_mock
        sh_mock.docker.assert_called_with('ps', _env=workflow.environment.data)
