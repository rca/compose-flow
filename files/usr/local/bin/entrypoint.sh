#!/bin/bash
set -e

PYPI_RC=$HOME/.pypirc

sed -i \
  -e "s/\${PYPI_USERNAME}/${PYPI_USERNAME}/g" \
  -e "s/\${PYPI_PASSWORD}/${PYPI_PASSWORD}/g" \
  ${PYPI_RC}

exec "$@"
