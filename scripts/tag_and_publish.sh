#!/bin/bash
set -e

tag-version --bump

version=$(tag-version)

tag-version write --pattern "(?P<start>.*?)0.0.0(?P<content>.*)" setup.py

python setup.py sdist
twine upload dist/*${version}*

git checkout setup.py
