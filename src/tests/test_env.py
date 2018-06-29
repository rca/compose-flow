import shlex
from unittest import TestCase, mock

from compose_flow.commands.subcommands.env import Env
from compose_flow.commands import ComposeFlow


class EnvTestCase(TestCase):
    def test_config_name_arg(self, *mocks):
        """
        Ensure the config arg updates the config name
        """
        command = shlex.split('-e dev --config-name=test env cat')
        flow = ComposeFlow(argv=command)
        env = Env(flow)

        self.assertEqual(env.config_name, 'test')

    @mock.patch('compose_flow.commands.compose_flow.PROJECT_NAME', new='testdirname')
    def test_default_config_name(self, *mocks):
        """
        Ensure the default config is given
        """
        command = shlex.split('-e dev env cat')
        flow = ComposeFlow(argv=command)
        env = Env(flow)

        self.assertEqual(env.config_name, 'dev-testdirname')
