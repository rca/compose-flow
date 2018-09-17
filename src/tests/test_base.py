from unittest import TestCase, mock

from compose_flow.commands.subcommands.base import BaseSubcommand


class TestSubcommand(BaseSubcommand):
    def fill_subparser(cls, parser):
        pass


@mock.patch('compose_flow.shell.sh')
class BaseTestCase(TestCase):
    def test_execute(self, *mocks):
        workflow = mock.Mock()
        command = TestSubcommand(workflow)

        proc = command.execute('docker ps')

        # make sure that sh was executed with the workflow environment
        sh_mock = mocks[-1]
        sh_mock.docker.assert_called_with('ps', _env=workflow.environment.data)
