#!/bin/bash
set -e

# Run migrations (ensure migrate_db.py exists and works)
# echo "Running migrations..."
# python migrate_db.py

# Start the application
echo "Starting Uvicorn server..."
# Using --host 0.0.0.0 to allow external access within container network
# Using --proxy-headers for running behind a proxy (e.g. Nginx/Cloud LB)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --reload --reload-include "*.json"
