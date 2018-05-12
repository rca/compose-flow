"""
Profile subcommand
"""
import os
import tempfile

from .base import BaseSubcommand

from dc_workflows.compose import get_overlay_filenames
from dc_workflows.config import get_config
from dc_workflows.utils import render


class Profile(BaseSubcommand):
    """
    Subcommand for managing profiles
    """
    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action')

    def cat(self):
        config = get_config()

        profile = config['profiles'][self.args.profile]

        fh = self.get_profile_compose_file(profile)

        print(fh.read())

    def get_profile_compose_file(self, profile):
        from .env import Env

        # load up the environment
        env = Env(self.workflow)

        os.environ.update(env.data)

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

    def handle(self):
        return self.handle_action()
