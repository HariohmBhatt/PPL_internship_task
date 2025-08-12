# Docker Local Setup — AI Quiz Microservice

This guide walks you through running the service locally using Docker Compose.

## Prerequisites

- Docker Desktop (Windows/macOS) or Docker Engine (Linux)
- Git (optional, if not already cloned)
- PowerShell (Windows) or Bash (macOS/Linux)

## TL;DR (Windows PowerShell)

```powershell
cd D:\Hariohm\PPL_internship_task
copy .env.example .env
docker compose up -d --build
Invoke-RestMethod http://localhost:8000/healthz
Invoke-RestMethod http://localhost:8000/readyz
```

Open the docs: http://localhost:8000/docs

## 1) Clone and enter the project (if needed)

```powershell
git clone <your-repo-url>
cd <your-repo-folder>
```

## 2) Environment configuration

Copy the example env and adjust as needed (optional for Docker defaults):

```powershell
copy .env.example .env
```

Notes:
- The Compose stack already sets `DATABASE_URL` for the API to reach the `db` service.
- To enable real AI, set one of the keys in `.env` (Compose auto-loads `.env`):
  - `OPENAI_API_KEY=sk-...`
  - `GEMINI_API_KEY=...`
- You can also set optional email settings if you want result emails.

## 3) Start the stack

```powershell
docker compose up -d --build
```

Services started:
- `db` (PostgreSQL 15, port 5432)
- `redis` (Redis 7, port 6379)
- `web` (FastAPI API, port 8000)

The API container runs DB migrations automatically before starting the server.

## 4) Verify health

```powershell
docker compose ps
docker compose logs -f db
docker compose logs -f web

Invoke-RestMethod http://localhost:8000/healthz
Invoke-RestMethod http://localhost:8000/readyz
```

Docs: http://localhost:8000/docs

## 5) Run the local test script (optional)

```powershell
./complete-test.ps1
```

This script covers: auth, health, quiz creation, submission, hints (with rate limit), retry, history, adaptive, leaderboard, caching, and (optionally) email config checks.

## 6) Postman collection

- Import from: `http://localhost:8000/postman-collection` or `http://localhost:8000/static/postman_collection.json`
- Create a Postman environment:
  - `BASE_URL = http://localhost:8000`
  - `TOKEN =` (leave empty; `POST /auth/login` will set it)

## 7) Common operations

```powershell
# View logs (follow)
docker compose logs -f web
docker compose logs -f db

# Re-run migrations (web does this on startup already)
docker compose exec web alembic upgrade head

# Seed a test user (optional)
docker compose exec web python create_test_user.py

# Stop services (keep data)
docker compose down

# Stop and remove volumes (wipe data)
docker compose down -v
```

## 8) Troubleshooting

- Port conflicts: ensure 8000 (API), 5432 (Postgres), 6379 (Redis) are free.
- DB not ready: wait for `db` healthcheck to pass; `web` depends on healthy `db` and `redis`.
- Ready check failing: inspect `docker compose logs -f web` and `-f db`, then retry `/readyz`.
- AI keys: without `OPENAI_API_KEY` or `GEMINI_API_KEY`, the service uses a Mock provider (still fully functional for dev/testing).
- Windows path issues: run commands from the project root so volume mounts resolve correctly.

## What’s running

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Postman Collection: http://localhost:8000/postman-collection


