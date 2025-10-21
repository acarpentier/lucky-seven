#!/bin/bash


# Change to src directory
cd /app/src

# Run migrations
echo "Running migrations..."
python manage.py migrate


# Start supervisord
echo "Starting supervisord..."
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
