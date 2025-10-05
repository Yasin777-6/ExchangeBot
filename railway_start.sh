#!/bin/bash

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn web server..."
exec gunicorn exchange.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --log-file -
