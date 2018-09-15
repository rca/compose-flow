import shlex

from unittest import TestCase, mock

from compose_flow import utils
from compose_flow.commands import Workflow

TEST_PROJECT_NAME = 'test_project_name'


@mock.patch('compose_flow.commands.workflow.PROJECT_NAME', new=TEST_PROJECT_NAME)
class WorkflowTestCase(TestCase):
    def test_sensible_defaults_no_env(self, *mocks):
        """
        Test sensible defaults when no environment is defined
        """
        command = shlex.split('publish')
        workflow = Workflow(argv=command)

        self.assertEqual(None, workflow.args.environment)
        self.assertEqual(None, workflow.args.remote)
        self.assertEqual(TEST_PROJECT_NAME, workflow.args.config_name)
        self.assertEqual(TEST_PROJECT_NAME, workflow.args.project_name)

    def test_sensible_defaults_with_env(self, *mocks):
        """
        Test sensible defaults when an environment is defined
        """
        env = 'dev'
        command = shlex.split(f'-e {env} publish')
        workflow = Workflow(argv=command)

        self.assertEqual(env, workflow.args.environment)
        self.assertEqual(env, workflow.args.remote)
        self.assertEqual(f'{env}-{TEST_PROJECT_NAME}', workflow.args.config_name)
        self.assertEqual(TEST_PROJECT_NAME, workflow.args.project_name)

    def test_sensible_defaults_with_env_and_project(self, *mocks):
        """
        Test sensible defaults when an environment and project name is defined
        """
        env = 'dev'
        command = shlex.split(f'-e {env} --project-name foo publish')
        workflow = Workflow(argv=command)

        self.assertEqual(env, workflow.args.environment)
        self.assertEqual(env, workflow.args.remote)
        self.assertEqual(f'{env}-foo', workflow.args.config_name)
        self.assertEqual('foo', workflow.args.project_name)
