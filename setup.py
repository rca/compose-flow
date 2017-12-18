#!/usr/bin/env python
from setuptools import setup


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
    scripts=['dc'],
    install_requires=[
        'PyYAML',
        'boltons',
        'sh',
    ]
)
