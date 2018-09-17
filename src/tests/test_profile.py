from unittest import TestCase, mock

from compose_flow.commands.subcommands.profile import Profile


class ProfileTestCase(TestCase):
    def setUp(self):
        self.workflow = mock.Mock()

    def test_profile_no_compose_dir(self, *mocks):
        """
        when there is no compose directory, do not attempt to render a profile
        """
        profile = Profile(self.workflow)

    def test_expand_services(self, *mocks):
        data = {
            'services': {
                'foo': {
                    'build': '..',
                    'image': '${DOCKER_IMAGE}',
                    'environment': [
                        'FOO=1',
                        'SPARK_WORKER_PORT=8888',
                        'SPARK_WORKER_WEBUI_PORT=8080',
                    ],
                    'ports': ['8000:8000'],
                    'deploy': {'replicas': 3},
                }
            },
            'compose_flow': {
                'expand': {
                    'foo': {
                        'increment': {
                            'env': ['SPARK_WORKER_PORT', 'SPARK_WORKER_WEBUI_PORT'],
                            'ports': {'source_port': True, 'destination_port': True},
                        }
                    }
                }
            },
        }

        profile = Profile(self.workflow)
        new_data = profile._check_cf_config(data)

        self.assertEqual(len(new_data['services']), 3)

        self.assertEqual(sorted(new_data['services'].keys()), ['foo1', 'foo2', 'foo3'])

        self.assertEqual(
            [x['ports'] for x in new_data['services'].values()],
            [['8000:8000'], ['8001:8001'], ['8002:8002']],
        )

        self.assertEqual(
            [x['environment'] for x in new_data['services'].values()],
            [
                ['FOO=1', 'SPARK_WORKER_PORT=8888', 'SPARK_WORKER_WEBUI_PORT=8080'],
                ['FOO=1', 'SPARK_WORKER_PORT=8889', 'SPARK_WORKER_WEBUI_PORT=8081'],
                ['FOO=1', 'SPARK_WORKER_PORT=8890', 'SPARK_WORKER_WEBUI_PORT=8082'],
            ],
        )

    @mock.patch('compose_flow.commands.subcommands.profile.open')
    def test_profile_writes_once(self, *mocks):
        open_mock = mocks[0]

        profile = Profile(self.workflow)
        profile.load = mock.Mock()

        profile.write()
        profile.write()
        profile.write()

        self.assertEqual(1, open_mock.call_count)
