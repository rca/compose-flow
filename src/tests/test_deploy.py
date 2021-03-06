import shlex

from unittest import mock

from compose_flow.commands import Workflow
from compose_flow.commands.subcommands.profile import Profile

from tests import BaseTestCase


@mock.patch('compose_flow.commands.subcommands.env.get_backend')
@mock.patch('compose_flow.commands.subcommands.env.os')
@mock.patch('compose_flow.commands.subcommands.profile.Profile.write')
class DeployTestCase(BaseTestCase):
    @mock.patch('compose_flow.commands.subcommands.env.Env.rw_env', new=True)
    @mock.patch('compose_flow.commands.subcommands.env.utils')
    def test_version_written(self, *mocks):
        """
        Ensures that version in env is written to the docker config
        """
        docker_mock = mocks[-1]
        docker_mock.get_config.return_value = (
            f"FOO=1\nBAR=2\nVERSION=1.0\nDOCKER_IMAGE=foo:dev"
        )

        utils_mock = mocks[0]
        utils_mock.get_tag_version.return_value = '0.0.1-test'
        utils_mock.render.side_effect = lambda x, **kwargs: x

        command = shlex.split('-e dev deploy')
        workflow = Workflow(argv=command)

        workflow.environment.write = mock.Mock()
        workflow.profile.check = mock.Mock()

        workflow.run()

        # make sure the environment write call is made
        workflow.environment.write.assert_called()

        # make sure the profile is checked
        workflow.profile.check.assert_called()

    @mock.patch('compose_flow.commands.subcommands.profile.Profile.data', new_callable=mock.PropertyMock)
    def test_checks_called(self, *mocks):
        """
        Ensure constraint checks are called on deploy
        """
        profile_data_mock = mocks[0]
        profile_data_mock.return_value = {
            'services': {
                'app': {
                    'image': 'foo:test',
                },
            },
        }
        command = shlex.split('-e dev deploy')
        workflow = Workflow(argv=command)

        workflow.environment.write = mock.Mock()

        # mock out all check methods
        all_checks = Profile.get_all_checks()
        self.assertEqual(3, len(all_checks), all_checks)

        for name in all_checks:
            _check_mock = mock.Mock()
            _check_mock.return_value = []

            setattr(workflow.profile, name, _check_mock)

        workflow.run()

        for name in all_checks:
            _check_mock = getattr(workflow.profile, name)

            self.assertGreater(_check_mock.call_count, 0, f'{name} not called')
