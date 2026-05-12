#!/usr/bin/env bash
# Render start script for native Python runtime

set -o errexit  # Exit on error

echo "Starting Gunicorn server..."
gunicorn --workers 2 \
         --bind 0.0.0.0:$PORT \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         --log-level info \
         app:app
