.PHONY: install dev lint format type test migrate new-migration run up down logs clean help

# Variables
PYTHON := python
PIP := pip
VENV := .venv
ACTIVATE := $(VENV)/Scripts/activate
APP_MODULE := app.main:app

# Default target
help:
	@echo "Available targets:"
	@echo "  install       - Install dependencies and setup pre-commit"
	@echo "  dev           - Run development server with auto-reload"
	@echo "  lint          - Run ruff linter"
	@echo "  format        - Format code with black and ruff"
	@echo "  type          - Run mypy type checking"
	@echo "  test          - Run tests with coverage"
	@echo "  migrate       - Run database migrations"
	@echo "  new-migration - Create new migration (use MESSAGE=description)"
	@echo "  run           - Run production server"
	@echo "  up            - Start services with docker-compose"
	@echo "  down          - Stop docker-compose services"
	@echo "  logs          - Show docker-compose logs"
	@echo "  clean         - Clean cache and build artifacts"

# Setup and dependencies
install:
	$(PIP) install -e ".[dev]"
	pre-commit install

# Development
dev:
	uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

# Code quality
lint:
	ruff check .

format:
	black .
	ruff check . --fix

type:
	mypy .

# Testing
test:
	pytest

# Database migrations
migrate:
	alembic upgrade head

new-migration:
	@if [ -z "$(MESSAGE)" ]; then \
		echo "Usage: make new-migration MESSAGE='description'"; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(MESSAGE)"

# Production
run:
	uvicorn $(APP_MODULE) --host 0.0.0.0 --port 8000

# Docker
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
