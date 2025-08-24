#!/bin/bash

# Start script for Syro Telegram Bot on Render

# Set default port if not provided
export PORT=${PORT:-8000}

echo "🚀 Starting Syro Telegram Bot..."
echo "📍 Port: $PORT"
echo "🌍 Environment: ${RENDER_SERVICE_NAME:-local}"

# Start the application
exec gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 1 \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --keep-alive 30 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile -
