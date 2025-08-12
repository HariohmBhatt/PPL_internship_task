# Important Files and Mappings – AI Quiz Microservice

This maps each task requirement to concrete files, symbols, endpoints, env, and status.

## Compact directory tree (relevant only)
```
app/
  main.py
  api/ auth.py quizzes.py hints.py history.py adaptive.py health.py leaderboard.py
  core/ config.py deps.py errors.py logging.py security.py
  db/ session.py migrations/env.py migrations/versions/001_initial_migration.py 002_add_leaderboard.py
  models/ base.py user.py quiz.py question.py submission.py answer.py evaluation.py retry.py leaderboard.py
  schemas/ auth.py quiz.py question.py submission.py history.py leaderboard.py
  services/
    ai/ provider.py openai_provider.py gemini_provider.py mock.py
    grading.py adaptive.py cache.py leaderboard.py notifications.py datetime.py
  static/postman_collection.json
Dockerfile  docker-compose.yml  render.yaml  alembic.ini  README.md  scripts/create_schema.sql
```

## Authentication (JWT)
- Files/symbols
  - `app/api/auth.py`: `login`, `register` – issues JWT, simple dev register
  - `app/core/security.py`: `create_access_token`, `verify_password`, `hash_password`
  - `app/core/deps.py`: `get_current_user` (extract/verify JWT); types `AuthUser`, `DBSession`
  - `app/core/config.py`: `Settings.jwt_secret`, `jwt_expire_minutes`
- Endpoint
  - POST `/auth/login` → `login` (auth.py)
  - POST `/auth/register` → `register` (auth.py)
- Env/config: `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`
- Status: implemented

## Quiz Lifecycle (create/get/questions/submit)
- Files/symbols
  - `app/api/quizzes.py`: `create_quiz`, `get_quiz`, `get_quiz_questions`, `submit_quiz`
  - `app/services/grading.py`: `GradingService.grade_submission`
  - Schemas: `app/schemas/quiz.py`, `app/schemas/question.py`, `app/schemas/submission.py`
- Endpoints
  - POST `/quizzes` → `create_quiz`
  - GET `/quizzes/{quiz_id}` → `get_quiz`
  - GET `/quizzes/{quiz_id}/questions` → `get_quiz_questions`
  - POST `/quizzes/{quiz_id}/submit` → `submit_quiz`
- Env/config: `CACHE_ENABLED`, `CACHE_TTL_SECONDS`, `REDIS_URL`
- Status: implemented

## Retry
- Files/symbols
  - `app/api/quizzes.py`: `retry_quiz`
  - `app/models/retry.py`: `Retry`
  - Schemas: `QuizRetryRequest`, `QuizRetryResponse` (schemas/quiz.py)
- Endpoint: POST `/quizzes/{quiz_id}/retry` → `retry_quiz`
- Env/config: —
- Status: implemented

## Hints (AI)
- Files/symbols
  - `app/api/hints.py`: `get_hint`, `reset_hint_usage`
  - AI provider: `app/services/ai/provider.py` (`get_ai_provider`, `AIProvider.hint`)
- Endpoint: POST `/quizzes/{quiz_id}/questions/{question_id}/hint` → `get_hint`
- Rate limit config: `HINT_RATE_LIMIT_PER_USER_QUESTION`
- Status: implemented (in‑memory counters). TODO: back with Redis for multi‑instance.

## Adaptive Difficulty
- Files/symbols
  - `app/api/adaptive.py`: `get_next_question`, `get_adaptive_status`
  - `app/services/adaptive.py`: `AdaptiveService` (window=3, step up/down/hold)
- Endpoints
  - POST `/quizzes/{quiz_id}/next` → `get_next_question`
  - GET `/quizzes/{quiz_id}/adaptive-status` → `get_adaptive_status`
- Env/config: —
- Status: implemented

## History & Filters (incl. date range)
- Files/symbols
  - `app/api/history.py`: `get_quiz_history`
  - `app/services/datetime.py`: `parse_date_range` (ISO or DD/MM/YYYY)
- Endpoint: GET `/quiz-history` → `get_quiz_history` (filters: grade, subject, min_marks, max_marks, from_date, to_date, completed_date, limit, offset)
- Env/config: —
- Status: implemented

## AI Providers & Suggestions
- Files/symbols
  - `app/services/ai/provider.py`: `AIProvider`, `get_ai_provider`
  - `app/services/ai/openai_provider.py`: `OpenAIProvider`
  - `app/services/ai/gemini_provider.py`: `GeminiProvider`
  - `app/services/ai/mock.py`: `MockProvider`
  - `app/services/grading.py`: calls `grade_short_answer` + `suggest_improvements`
- Used by endpoints
  - POST `/quizzes` (generate questions)
  - POST `/quizzes/{quiz_id}/submit` (grade + suggestions)
  - POST `/quizzes/{quiz_id}/questions/{question_id}/hint` (hint)
- Env/config: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL`, `ENV`
- Status: implemented (Mock by default if no keys)

## Database (models + Alembic + SQL)
- Files/symbols
  - Models: `app/models/*.py` (`User`, `Quiz`, `Question`, `Submission`, `Answer`, `Evaluation`, `Retry`, `LeaderboardEntry`)
  - Alembic: `alembic.ini`, `app/db/migrations/env.py`, `versions/001_initial_migration.py`, `002_add_leaderboard.py`
  - Session: `app/db/session.py` (`create_tables` on startup)
  - SQL: `scripts/create_schema.sql` (raw schema)
- Status: implemented

## Health/Readiness
- Files/symbols
  - `app/api/health.py`: `health_check`, `readiness_check`
- Endpoints
  - GET `/healthz` → `health_check`
  - GET `/readyz` → `readiness_check`
- Status: implemented

## Config (.env/.settings)
- Files/symbols
  - `app/core/config.py`: `Settings`, `cors_origins`, `is_development/is_testing/is_production`
  - `.env.example`: sample envs
- Env: `JWT_SECRET`, `DATABASE_URL`, `ALLOWED_ORIGINS`, `ENV`, `LOG_LEVEL`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `REDIS_URL`, `CACHE_ENABLED`, `CACHE_TTL_SECONDS`, `NOTIFICATION_ENABLED`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `NOTIFICATION_FROM_EMAIL`
- Status: implemented

## Hosting (Dockerfile, Compose, Render)
- Files
  - `Dockerfile` (slim runtime), `docker-compose.yml` (db, redis, web), `render.yaml` (web+db+redis), `start.py`, `start.sh`
- Status: implemented

## Postman/Docs
- Files
  - `app/static/postman_collection.json`; served via `app/main.py` at `/postman-collection`, `/static/postman_collection.json`
  - `README.md`
- Status: implemented

## Bonus: Leaderboard / Cache / Email
- Files/symbols
  - Leaderboard: `app/api/leaderboard.py` (`get_leaderboard`, `get_my_rank`, `get_available_subjects`, `get_available_grades`)
  - Redis cache: `app/services/cache.py` (used in quizzes/leaderboard)
  - Email: `app/services/notifications.py` (used in `submit_quiz`)
- Endpoints: GET `/leaderboard`, `/leaderboard/my-rank`, `/leaderboard/subjects`, `/leaderboard/grades`
- Env: `REDIS_URL`, `CACHE_ENABLED`, `CACHE_TTL_SECONDS`, `NOTIFICATION_ENABLED`, `SMTP_*`
- Status: implemented

---

### codeindex.json
A machine-readable index is generated at `docs/codeindex.json`.
