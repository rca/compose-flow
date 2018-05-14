import logging
import os
import tempfile

import yaml

from .config import DC_CONFIG_ROOT
from .utils import remerge, render


def get_overlay_filenames(overlay):
    logger = logging.getLogger('get_overlay_filenames')

    overlay_filenames = []

    applied = []
    for item in overlay:
        if item in applied:
            continue

        applied.append(item)

        path = None
        if isinstance(item, dict):
            name = item['name']
            path = item['path']
        else:
            name = item

        # join path and name if the path is given
        if path:
            _filename = os.path.join(path, name)
        else:
            _filename = name

        if _filename and os.path.exists(_filename) and os.path.isfile(_filename):
            overlay_filenames.append(_filename)
        else:
            # prefix partial with a dot in order to complete the name
            if name:
                name = '.{}'.format(name)
            else:
                name = ''

            _filename = 'docker-compose{}.yml'.format(name)
            if path:
                _filename = os.path.join(path, _filename)

            logging.debug('_filename={}'.format(_filename))

            if os.path.exists(_filename):
                overlay_filenames.append(_filename)
            else:
                logger.warning(f'filename={_filename} does not exist, skipping')

    # check to see if any filenames were found, else default to docker-compose.yml
    if not overlay_filenames:
        overlay_filenames.append('docker-compose.yml')

    return overlay_filenames
