import logging

from functools import lru_cache

import sh

from .base import BaseSubcommand
# from .compose import Compose


class Publish(BaseSubcommand):
    """
    Subcommand for building and pushing Docker images
    """
    rw_env = True
    remote_action = True

    def build(self):
        compose = self.compose

        compose.handle(extra_args=['build'])

    @property
    @lru_cache()
    def compose(self):
        """
        Returns a Compose subcommand
        """
        from .compose import Compose

        return Compose(self.workflow)

    def do_validate_profile(self):
        return False

    @classmethod
    def fill_subparser(cls, parser, subparser) -> None:
        pass

    def handle(self):
        # only load up the basic environment for publish
        self.update_runtime_environment(load_cf_env=False)

        self.build()

        self.push()

    def is_missing_env_arg_okay(self):
        return True

    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def push(self):
        docker_images = set()

        profile = self.workflow.profile
        for service_data in profile.data['services'].values():
            if service_data.get('build'):
                docker_images.add(service_data.get('image'))

        for docker_image in docker_images:
            if len(docker_images) > 1:
                self.logger.info(f'pushing {docker_image}')

            if self.args.dry_run:
                self.logger.info(f'docker push {docker_image}')
            else:
                sh.docker('push', docker_image, _fg=True)
