import os

CF_DOCKER_IMAGE_PREFIX = 'test.registry.prefix.com'

os.environ['CF_DOCKER_IMAGE_PREFIX'] = CF_DOCKER_IMAGE_PREFIX
