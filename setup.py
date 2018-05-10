#!/usr/bin/env python
from setuptools import find_packages, setup

SRC_PREFIX = 'src'

packages = find_packages(SRC_PREFIX)

def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='dc-workflows',
    url='https://github.com/rca/dc',
    author='Roberto Aguilar',
    author_email='roberto.c.aguilar@gmail.com',
    version='0.0.0',
    description='codified workflows for docker compose',
    long_description=readme(),
    package_dir={'':'src'},
    packages=packages,
    entry_points={
        'console_scripts': [
            'dc = dc_workflows.entrypoints:dc',
        ],
    },
    install_requires=[
        'PyYAML',
        'boltons',
        'sh',
        'tag-version',
    ]
)
