
from .base import BaseBuildSubcommand


class Publish(BaseBuildSubcommand):
    """
    Subcommand for building and pushing Docker images
    """

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

    def push(self):
        docker_images = self.get_built_docker_images()
        for docker_image in docker_images:
            if len(docker_images) > 1:
                self.logger.info(f'pushing {docker_image}')

            if self.workflow.args.dry_run:
                self.logger.info(f'docker push {docker_image}')
            else:
                self.execute_publish(docker_image)

    def execute_publish(self, tagged_image_name: str):
        self.execute(f'docker push {tagged_image_name}', _fg=True)

    def handle(self):
        self.build(pull=False)

        self.push()
