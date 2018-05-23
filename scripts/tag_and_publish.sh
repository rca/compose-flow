#!/bin/bash
set -e

SCRIPT_DIR=$(dirname $0)

tag-version --bump

${SCRIPT_DIR}/publish.sh
