import shlex
from unittest import TestCase, mock

from compose_flow import utils
from compose_flow.commands.subcommands.env import Env
from compose_flow.commands import Workflow

from tests import BaseTestCase


@mock.patch('compose_flow.commands.workflow.PROJECT_NAME', new='testdirname')
class EnvTestCase(BaseTestCase):
    def test_backend_default(self, *mocks):
        """
        Ensure a local backend is returned
        """
        flow = mock.Mock()
        flow.args.remote = None

        env = Env(flow)

        self.assertEqual(env.backend.__class__.__name__, 'LocalBackend')

    @mock.patch('compose_flow.commands.subcommands.env.get_backend')
    def test_backend_from_app_config(self, *mocks):
        """
        Ensure a local backend is returned
        """
        backend_name = 'swarm'

        flow = mock.Mock()
        flow.args.remote = 'dev'

        flow.app_config = {
            'remotes': {
                'dev': {
                    'environment': {
                        'backend': backend_name,
                    },
                },
            },
        }

        get_backend_mock = mocks[0]
        get_backend_mock.return_value = 'SwarmBackend'

        env = Env(flow)
        backend = env.backend

        self.assertEqual(backend, 'SwarmBackend')

        get_backend_mock.assert_called_with(backend_name, workflow=flow)

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

    @mock.patch('compose_flow.commands.subcommands.env.get_backend')
    def test_load_ro(self, *mocks):
        """
        Ensures that env.load does not reset the VERSION var

        The DOCKER_IMAGE and VERSION vars should only be modified when publishing an image
        In all other commands, the environment should be read-only
        """
        version = '1.2.3'
        docker_image = 'foo:bar'

        get_backend_mock = mocks[0]
        get_backend_mock.return_value.read.return_value = (
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
