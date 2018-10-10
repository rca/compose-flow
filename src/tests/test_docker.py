from unittest import TestCase, mock

from compose_flow import docker


class DockerTestCase(TestCase):
    def test_json_formatter_context(self, *mocks):
        """
        Ensures the JSON format context manager does the right thing
        """
        with docker.json_formatter('docker node ls') as json_command:
            self.assertEqual('docker node ls --format "{{ json . }}"', json_command)
