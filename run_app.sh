#!/bin/bash

# Load environment variables from .env
export $(cat .env | xargs)

echo "Starting Redis server..."
redis-server &  # Run Redis in the background
REDIS_PID=$!

echo "Starting Celery worker..."
celery -A app.celery worker --loglevel=info --concurrency=4&  # Run Celery in the background
CELERY_PID=$!

# Trap to ensure services are stopped on script termination
trap "echo 'Shutting down services...'; kill $REDIS_PID $CELERY_PID; exit" SIGINT SIGTERM

echo "Starting Flask app..."
docai_venv/bin/python app.py  # Run Flask app in the foreground

echo "Shutting down services..."
kill $REDIS_PID $CELERY_PID