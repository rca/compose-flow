import logging

from functools import lru_cache

import sh

from .base import BaseSubcommand
# from .compose import Compose


class Publish(BaseSubcommand):
    """
    Subcommand for building and pushing Docker images
    """
    def build(self):
        self.compose.run(compose_args=['build'])

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
        docker_image = self.env.data['DOCKER_IMAGE']

        if self.args.dry_run:
            self.logger.info(f'docker push {docker_image}')
        else:
            sh.docker('push', docker_image, _fg=True)
