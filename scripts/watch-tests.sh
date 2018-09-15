#!/bin/bash
set -e

watchmedo shell-command --recursive --ignore-directories --drop --wait -c 'nosetests src/' src/
