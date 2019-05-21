import json
from unittest import TestCase, mock

import semver

from compose_flow.errors import PublishAutoTagsError
from compose_flow.image import PrivateImage
from tests.utils import get_content


class PrivateImageMixin:
    _default_repository = 'my-registry.foobar.org'
    _default_image_name = 'tompose-flow'
    _default_tag = '3.5.9'
    _default_tagged_image_name = f'{_default_repository}/{_default_image_name}:{_default_tag}'

    def _get_private_image(self, tagged_image_name: str = None):
        """
        Return a private image instance
        """
        tagged_image_name = tagged_image_name or self._default_tagged_image_name
        return PrivateImage(tagged_image_name=tagged_image_name, publish_callable=mock.MagicMock(),
                            tag_callable=mock.MagicMock())


class PrivateImageHappyPathTestCase(PrivateImageMixin, TestCase):

    @mock.patch('compose_flow.image.requests.Session.get')
    @mock.patch('compose_flow.commands.subcommands.base.BaseSubcommand.execute')
    def test_e2e_publish_auto_tags(self, *mocks):
        """
        Test that we can publish and auto-tag an image.
        """
        mocks[1].return_value.json.return_value = json.loads(get_content('registry_tags_response.json'))
        private_image = self._get_private_image()
        private_image.publish_with_auto_tags()

        major_tagged_image_name = f'{self._default_repository}/{self._default_image_name}:3'
        minor_tagged_image_name = f'{self._default_repository}/{self._default_image_name}:3.5'
        target_publish_call_args = [
            (self._default_tagged_image_name),
            (major_tagged_image_name),
            (minor_tagged_image_name),
        ]
        publish_callable_mock = private_image._publish_callable
        for call_args in target_publish_call_args:
            publish_callable_mock.assert_any_call(call_args)

        target_tag_call_args = [
            (self._default_tagged_image_name, major_tagged_image_name),
            (self._default_tagged_image_name, minor_tagged_image_name),
        ]
        tag_callable_mock = private_image._tag_callable
        for call_args in target_tag_call_args:
            tag_callable_mock.assert_any_call(*call_args)

    def test_ut_image_name(self, *mocks):
        """Ensure PrivateImage populates name."""
        private_image = self._get_private_image()
        self.assertEqual(self._default_image_name, private_image.name)

    def test_ut_repository(self, *mocks):
        """Ensure PrivateImage populates repository."""
        private_image = self._get_private_image()
        self.assertEqual(self._default_repository, private_image.repository)

    def test_ut_tag_version_info(self, *mocks):
        """Ensure PrivateImage populates tag_version_info"""
        private_image = self._get_private_image()
        target_version_info = semver.VersionInfo.parse(self._default_tag)
        self.assertEqual(target_version_info, private_image.version_info)

    @mock.patch('compose_flow.image.PrivateImage._get_published_tags')
    def test_ut__get_latest_published_version(self, *mocks):
        """Ensure PrivateImage can find the most recently published tag"""
        mocks[0].return_value = json.loads(get_content('registry_tags_response.json')).get('tags')
        private_image = self._get_private_image()
        target_latest_published_version = semver.VersionInfo.parse('3.5.8')
        latest_published_version = private_image._get_latest_published_version()
        self.assertEqual(target_latest_published_version, latest_published_version)

    @mock.patch('compose_flow.image.requests.Session.get')
    def test_ut__get_published_tags(self, *mocks):
        """Ensure we appropriately process the docker registry tags response"""
        mocks[0].return_value.json.return_value = json.loads(get_content('registry_tags_response.json'))
        private_image = self._get_private_image()
        target_tags = json.loads(get_content('registry_tags_response.json')).get('tags')
        published_tags = private_image._get_published_tags(private_image.name)
        self.assertEqual(target_tags, published_tags)

    def test_ut_official_release(self, *mocks):
        """
        Ensure official release property happy path works.
        """
        private_image = self._get_private_image()
        self.assertEqual(True, private_image.official_release)

    def test_ut_publish(self, *mocks):
        """Ensure `publish` publishes the original private image"""
        private_image = self._get_private_image()
        private_image.publish()
        self.assertEqual(
            private_image._publish_callable.call_args[0][0],
            private_image._get_tagged_image_name(self._default_tag)
        )

    def test_ut_publish_major(self, *mocks):
        """Ensure `publish_major` tags and publishes desired tag"""
        private_image = self._get_private_image()
        private_image._publish_major()
        target_tagged_image_name = f'{self._default_repository}/{self._default_image_name}:3'
        private_image._tag_callable.assert_any_call(*(self._default_tagged_image_name, target_tagged_image_name))
        private_image._publish_callable.assert_any_call(target_tagged_image_name)

    def test_ut_publish_minor(self, *mocks):
        """Ensure `publish_minor` tags and publishes desired tag"""
        private_image = self._get_private_image()
        private_image._publish_minor()
        target_tagged_image_name = f'{self._default_repository}/{self._default_image_name}:3.5'
        private_image._tag_callable.assert_any_call(*(self._default_tagged_image_name, target_tagged_image_name))
        private_image._publish_callable.assert_any_call(target_tagged_image_name)


class PrivateImageSadPathTestCase(PrivateImageMixin, TestCase):

    def test_e2e_invalid_publish_with_auto_tags(self, *mocks):
        """Ensure unhappy path works as we expect"""
        bad_tag = '2.0.3-999-385uegfd-feature--21345-foo-bar-baz'
        invalid_tagged_image_name = f'{self._default_repository}/{self._default_image_name}:{bad_tag}'
        private_image = self._get_private_image(invalid_tagged_image_name)
        with self.assertRaises(PublishAutoTagsError):
            private_image.publish_with_auto_tags()
