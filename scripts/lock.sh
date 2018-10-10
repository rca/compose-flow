#!/bin/bash

DOCKER_IMAGE=python:3.6
PYPI_URL=https://pypi.osslabs.net/repo/oss/

docker run -v $PWD/:/root -e PIP_EXTRA_INDEX_URL=$PYPI_URL --rm $DOCKER_IMAGE bash -c 'pip install pipenv && cd $HOME && pipenv lock --pre'
