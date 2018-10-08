import logging

from functools import lru_cache

from .base import BaseSubcommand


class Publish(BaseSubcommand):
    """
    Subcommand for building and pushing Docker images
    """

    rw_env = True
    remote_action = True
    update_version_env_vars = True

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

    def get_built_docker_images(self) -> list:
        """
        Returns a list of docker images built in the compose file
        """
        docker_images = set()

        profile = self.workflow.profile
        for service_data in profile.data['services'].values():
            if service_data.get('build'):
                docker_images.add(service_data.get('image'))

        return list(docker_images)

    def handle(self):
        self.build()

        self.push()

    def is_missing_env_arg_okay(self):
        return True

    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def push(self):
        docker_images = self.get_built_docker_images()
        for docker_image in docker_images:
            if len(docker_images) > 1:
                self.logger.info(f'pushing {docker_image}')

            if self.workflow.args.dry_run:
                self.logger.info(f'docker push {docker_image}')
            else:
                self.execute(f'docker push {docker_image}', _fg=True)
