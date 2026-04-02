#!/usr/bin/env bash
# Render build script — runs before the server starts

set -o errexit  # Exit on any error

pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py migrate
