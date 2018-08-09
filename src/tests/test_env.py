import shlex
from unittest import TestCase, mock

from compose_flow import utils
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

    @mock.patch('compose_flow.commands.subcommands.env.docker')
    def test_load_ro(self, *mocks):
        """
        Ensures that env.load does not reset the VERSION var

        The DOCKER_IMAGE and VERSION vars should only be modified when publishing an image
        In all other commands, the environment should be read-only
        """
        docker_mock = mocks[0]
        docker_mock.get_config.return_value = "FOO=1\nBAR=2\nVERSION=1.2.3"

        command = shlex.split('-e dev env cat')
        flow = ComposeFlow(argv=command)

        flow.run()

        env = flow.subcommand

        self.assertEqual('1.2.3', env.data['VERSION'])

    @mock.patch('compose_flow.commands.subcommands.env.Env.rw_env', new=True)
    @mock.patch('compose_flow.commands.subcommands.env.utils')
    @mock.patch('compose_flow.commands.subcommands.env.docker')
    def test_load_rw(self, *mocks):
        """
        Ensures that env.load sets the VERSION var
        """
        docker_mock = mocks[0]
        docker_mock.get_config.return_value = "FOO=1\nBAR=2\nVERSION=1.2.3"

        utils_mock = mocks[1]
        utils_mock.get_tag_version.return_value = '0.9.999'
        utils_mock.render = utils.render

        command = shlex.split('-e dev env cat')
        flow = ComposeFlow(argv=command)

        flow.run()

        env = flow.subcommand

        self.assertEqual(utils_mock.get_tag_version.return_value, env.data['VERSION'])
