#!/bin/bash

# AI Quiz Microservice Startup Script for Render.com

set -e  # Exit on any error

echo "Starting AI Quiz Microservice..."

# Wait for database to be ready
echo "Waiting for database connection..."
python -c "
import time
import psycopg
from app.core.config import get_settings

settings = get_settings()
max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        # Extract connection parameters from DATABASE_URL
        conn = psycopg.connect(settings.database_url)
        conn.close()
        print('Database connection successful!')
        break
    except Exception as e:
        retry_count += 1
        print(f'Database connection attempt {retry_count}/{max_retries} failed: {e}')
        time.sleep(2)

if retry_count >= max_retries:
    print('Failed to connect to database after maximum retries')
    exit(1)
"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
