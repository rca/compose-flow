#!/bin/bash
set -e

SCRIPT_DIR=$(dirname $0)

tag-version --bump

bash ${SCRIPT_DIR}/publish.sh
