#!/usr/bin/env python3
"""
Startup script for AI Quiz Microservice.
Handles database migrations and starts the FastAPI application.
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def wait_for_database():
    """Wait for database to be ready."""
    logger.info("Waiting for database connection...")
    
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Import here to avoid issues if modules aren't available yet
            import psycopg
            from app.core.config import get_settings
            
            settings = get_settings()
            
            # Test database connection
            conn = psycopg.connect(settings.database_url)
            conn.close()
            logger.info("Database connection successful!")
            return True
            
        except Exception as e:
            retry_count += 1
            logger.info(f"Database connection attempt {retry_count}/{max_retries} failed: {e}")
            time.sleep(2)
    
    logger.error("Failed to connect to database after maximum retries")
    return False

def run_migrations():
    """Run database migrations."""
    logger.info("Running database migrations...")
    
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Database migrations completed successfully")
        logger.debug(f"Migration output: {result.stdout}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e}")
        logger.error(f"Migration error output: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("Alembic not found. Make sure it's installed.")
        return False

def start_application():
    """Start the FastAPI application."""
    logger.info("Starting FastAPI application...")
    
    # Get port from environment or default to 8000
    port = os.getenv("PORT", "8000")
    
    # Start uvicorn
    try:
        subprocess.run([
            "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", port,
            "--workers", "1"
        ], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")

def main():
    """Main startup function."""
    logger.info("Starting AI Quiz Microservice...")
    
    # Check if we're in the right directory
    if not Path("app").exists():
        logger.error("app directory not found. Make sure you're in the project root.")
        sys.exit(1)
    
    # Wait for database (with timeout)
    if not wait_for_database():
        logger.error("Database connection failed. Exiting.")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        logger.error("Database migrations failed. Exiting.")
        sys.exit(1)
    
    # Start the application
    start_application()

if __name__ == "__main__":
    main()
