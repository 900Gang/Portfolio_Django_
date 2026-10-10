#!/usr/bin/env bash
set -o errexit

# requirements.lock pins every package with its hashes (generated from
# requirements.txt; see README "Dependencies"). Wheels only, so no package
# setup script runs during the build.
pip install --require-hashes --only-binary :all: -r requirements.lock

python manage.py collectstatic --noinput
python manage.py migrate