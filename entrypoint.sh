#!/bin/bash
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting Django application..."
exec python manage.py runserver 0.0.0.0:8000
