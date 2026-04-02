#!/bin/bash
python manage.py migrate
gunicorn videoconferencing.wsgi
