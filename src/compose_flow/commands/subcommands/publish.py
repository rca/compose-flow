import logging

from functools import lru_cache

import sh

from .base import BaseSubcommand
# from .compose import Compose

from compose_flow.errors import CommandError


class Publish(BaseSubcommand):
    """
    Subcommand for building and pushing Docker images
    """
    def build(self):
        self.compose.run(extra_args=['build'])

    @property
    @lru_cache()
    def compose(self):
        """
        Returns a Compose subcommand
        """
        from .compose import Compose

        return Compose(self.workflow)

    @classmethod
    def fill_subparser(cls, parser, subparser) -> None:
        pass

    def handle(self):
        self.build()

        self.push()

    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def push(self):
        # infer the registry from the DOCKER_IMAGE env var
        registry = None
        env_docker_image = self.env.data['DOCKER_IMAGE']
        if '/' in env_docker_image:
            registry = env_docker_image.split('/', 1)[0]

        docker_images = set()
        for service_data in self.profile.data['services'].values():
            docker_images.add(service_data.get('image'))

        if registry is None and len(docker_images) > 1:
            raise CommandError('multiple docker images detected and registry is unknown')

        for docker_image in docker_images:
            if not docker_image.startswith(registry):
                print(f'skipping {docker_image}')

                continue

            if len(docker_images) > 1:
                print(docker_image)

            if self.args.dry_run:
                self.logger.info(f'docker push {docker_image}')
            else:
                sh.docker('push', docker_image, _fg=True)
