"""
Profile subcommand
"""
import os
import tempfile

import yaml

from .base import BaseSubcommand

from dc_workflows.compose import get_overlay_filenames
from dc_workflows.config import get_config
from dc_workflows.errors import NoSuchProfile
from dc_workflows.utils import remerge, render

# keep track of written profiles in order to prevent writing them twice
WRITTEN_PROFILES = []


class Profile(BaseSubcommand):
    """
    Subcommand for managing profiles
    """
    @property
    def filename(self) -> str:
        """
        Returns the filename for this profile
        """
        return f'docker-compose-dc-{self.args.profile}.yml'

    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action')

    def cat(self):
        """
        Prints the loaded compose file to stdout
        """
        print(self.load())

    def get_profile_compose_file(self, profile):
        """
        Processes the profile to generate the compose file
        """
        os.environ.update(self.env.data)

        filenames = get_overlay_filenames(profile)

        # merge multiple files together so that deploying stacks works
        # https://github.com/moby/moby/issues/30127
        if len(filenames) > 1:
            yaml_contents = []

            for item in filenames:
                with open(item, 'r') as fh:
                    yaml_contents.append(yaml.load(fh))

            merged = remerge(yaml_contents)
            content = yaml.dump(merged, default_flow_style=False)
        else:
            with open(filenames[0], 'r') as fh:
                content = fh.read()

        # render the file
        rendered = render(content)

        fh = tempfile.TemporaryFile(mode='w+')

        fh.write(rendered)
        fh.flush()

        fh.seek(0, 0)

        return fh

    def load(self) -> str:
        """
        Loads the compose file that is generated from all the items listed in the profile
        """
        config = get_config()

        profile_name = self.args.profile
        try:
            profile = config['profiles'][profile_name]
        except KeyError:
            raise NoSuchProfile(f'profile={profile_name}')

        fh = self.get_profile_compose_file(profile)

        return fh.read()

    def write(self) -> None:
        """
        Writes the loaded compose file to disk
        """
        # do not write profiles more than once per execution
        if self.filename in WRITTEN_PROFILES:
            return

        with open(self.filename, 'w') as fh:
            fh.write(self.load())

        WRITTEN_PROFILES.append(self.filename)
