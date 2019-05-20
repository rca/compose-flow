from functools import lru_cache
from typing import Callable

import requests
import semver

from compose_flow.errors import PublishAutoTagsError
from compose_flow.settings import PRIVATE_REGISTRY_USER, PRIVATE_REGISTRY_PASSWORD


class AbstractImage:
    pass


class PrivateImage(AbstractImage):

    def __init__(self, tagged_image_name: str = None, publish_callable: Callable = None, tag_callable: Callable = None):
        """
        Init method
        :param tagged_image_name: A fully qualified image name of format repository/image_name:tag
        :param publish_callable: A callable that accepts a fully qualified image name as its only argument
                    and publishes it
        :param tag_callable: A callable that accepts fully qualified image names as arguments and tags the image
                referenced by the first string with the second string
        """
        self._tagged_image_name = tagged_image_name
        self._parse_tagged_image_name()

        self._publish_callable = publish_callable
        self._tag_callable = tag_callable

    def can_publish_with_auto_tags(self):
        """Return whether or not we can publish with auto tags."""
        semver_components_clean = [self.version_info.major, self.version_info.minor, self.version_info.patch]
        semver_components_dirty = [self.version_info.prerelease, self.version_info.build]
        return all(semver_components_clean) and not any(semver_components_dirty)

    def _get_latest_published_version(self):
        """Take a list of tags and return the most recent"""
        published_tags = self._get_published_tags()
        semver_published_tags = []
        for tag in published_tags:
            try:
                version_info = semver.VersionInfo.parse(tag)
                semver_published_tags.append(version_info)
            except ValueError:
                continue
        sorted_semver_published_tags = sorted(semver_published_tags, reverse=True)
        if sorted_semver_published_tags:
            return sorted_semver_published_tags[0]
        else:
            return None

    def _get_published_tags(self) -> list():
        """
        Return a list of published tags from the repository/registry
        """
        url = f'https://{self.repository}/v2/{self.name}/tags/list'
        session = requests.Session()
        response = session.get(url, auth=requests.auth.HTTPBasicAuth(PRIVATE_REGISTRY_USER, PRIVATE_REGISTRY_PASSWORD))
        tags = response.json().get('tags')
        return tags

    def _get_tagged_image_name(self, tag: str = None):
        """Utility for getting a tagged image name"""
        tag = tag or self.tag
        return f'{self.repository}/{self.name}:{tag}'

    def _parse_tagged_image_name(self):
        """
        Parse the tagged_image_name and set repository, image_name, semver version_info
        :return:
        """
        self.repository = self._tagged_image_name.split('/')[0] if '/' in self._tagged_image_name else None
        assert self.repository, (
            f'Invalid repository value of {self.repository}.' 
            'Private images must have a repository set.'
        )
        self.tag = self._tagged_image_name.split(':')[1] if ':' in self._tagged_image_name else None
        self.name = self._tagged_image_name.lstrip(f'{self.repository}/').rstrip(f':{self.tag}')
        try:
            self.version_info = semver.VersionInfo.parse(self.tag)
        except ValueError:
            self.version_info = None

    def publish_with_auto_tags(self):
        """Publish an image and auto-tag major and minor releases"""
        if self.can_publish_with_auto_tags():
            latest_version = self._get_latest_published_version()
            if latest_version < self.version_info:
                self.publish()
                self._publish_major()
                self._publish_minor()
            else:
                self.logger.warning(f'Publishing with auto tags is only allowed for most recent tags')
        else:
            raise PublishAutoTagsError(
                f'Publishing with auto tags is only allowed for images tagged with a MAJOR.MINOR.PATCH semver'
            )

    def publish(self):
        """Publish the private image"""
        self._publish(self.version_info)

    def _publish(self, tag: str):
        tagged_image_name = self._get_tagged_image_name(tag)
        self._publish_callable(tagged_image_name)

    def _publish_major(self):
        """Publish image tagged to major version"""
        tag = self.version_info.major
        self._tag(tag)
        self._publish(tag)

    def _publish_minor(self):
        """Publish image tagged to major.minor version"""
        tag = f'{self.version_info.major}.{self.version_info.minor}'
        self._tag(tag)
        self._publish(tag)

    def _tag(self, tag: str):
        """Tag the private image with a new tag"""
        tagged_image_name = self._get_tagged_image_name(tag)
        self._tag_callable(self._tagged_image_name, tagged_image_name)
