import shlex
from unittest import TestCase, mock

from compose_flow import utils
from compose_flow.commands.subcommands.env import Env
from compose_flow.commands import Workflow

from tests import BaseTestCase


@mock.patch('compose_flow.commands.workflow.PROJECT_NAME', new='testdirname')
class EnvTestCase(BaseTestCase):
    def test_config_name_arg(self, *mocks):
        """
        Ensure the config arg updates the config name

        TODO: this should move to test_workflow
        """
        command = shlex.split('-e dev --config-name=test env cat')
        flow = Workflow(argv=command)
        env = Env(flow)

        self.assertEqual(flow.config_name, 'test')

    def test_data_not_loaded_when_cache_is_empty_dict(self, *mocks):
        workflow = mock.MagicMock()
        workflow.args.environment = None
        workflow.args.iter.return_value = []

        env = Env(workflow)

        # setup mocks on the env instance
        env.load = mock.Mock()
        env.load.return_value = {}

        # prime the cache with an empty dict to ensure load is not called
        env._data = {}

        env.data

        env.load.assert_not_called()

    def test_default_config_name(self, *mocks):
        """
        Ensure the default config is given

        TODO: this should move to test_workflow
        """
        command = shlex.split('-e dev env cat')
        flow = Workflow(argv=command)
        env = Env(flow)

        self.assertEqual(flow.config_name, 'dev-testdirname')

    @mock.patch('compose_flow.commands.subcommands.env.docker')
    def test_load_ro(self, *mocks):
        """
        Ensures that env.load does not reset the VERSION var

        The DOCKER_IMAGE and VERSION vars should only be modified when publishing an image
        In all other commands, the environment should be read-only
        """
        version = '1.2.3'
        docker_image = 'foo:bar'

        docker_mock = mocks[0]
        docker_mock.get_config.return_value = (
            f"FOO=1\nBAR=2\nVERSION={version}\nDOCKER_IMAGE={docker_image}"
        )

        command = shlex.split('-e dev env cat')
        flow = Workflow(argv=command)

        flow.run()

        env = flow.subcommand

        self.assertEqual(version, env.data['VERSION'])
        self.assertEqual(docker_image, env.data['DOCKER_IMAGE'])

        self.assertEqual(
            ['BAR', 'DOCKER_IMAGE', 'FOO', 'VERSION'], sorted(env._persistable_keys)
        )

    @mock.patch('compose_flow.commands.subcommands.env.Env.rw_env', new=True)
    @mock.patch('compose_flow.commands.subcommands.env.utils')
    @mock.patch('compose_flow.commands.subcommands.env.docker')
    def test_update_version(self, *mocks):
        """
        Ensures that version in env is updated when the publish command is run
        """
        version = '1.2.3'
        new_version = '0.9.999'
        docker_image = 'foo:bar'

        docker_mock = mocks[0]
        docker_mock.get_config.return_value = (
            f"FOO=1\nBAR=2\nVERSION={version}\nDOCKER_IMAGE={docker_image}"
        )

        utils_mock = mocks[1]
        utils_mock.get_tag_version.return_value = new_version
        utils_mock.render = utils.render

        command = shlex.split('-e dev publish')
        flow = Workflow(argv=command)

        env = Env(flow)

        env.update_workflow_env()

        self.assertEqual(utils_mock.get_tag_version.return_value, env.data['VERSION'])
        self.assertEqual(f'test.registry.prefix.com/testdirname:{new_version}', env.data['DOCKER_IMAGE'])
