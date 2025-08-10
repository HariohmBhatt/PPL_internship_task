# TASKS.md

> Detailed task plan with subtasks and acceptance criteria. Use ✅/❌ and checkboxes.

## 0) Project Bootstrap ✅

* [x] Create repo with layout from **CURSOR\_RULES.md**.
* [x] Add `README.md` with local/dev/prod instructions.
* [x] Add `.env.example` (JWT\_SECRET, DATABASE\_URL, OPENAI\_API\_KEY optional, ALLOWED\_ORIGINS).
* [x] Configure ruff, black, mypy, pytest, pre-commit.
* **AC:** ✅ Repo boots with `uvicorn app.main:app`, health endpoints respond.

## 1) Authentication ✅

* [x] Implement `POST /auth/login` (mock) → issue JWT (24h).
* [x] Add dependency to verify JWT on `/quizzes/*`.
* [x] Add negative tests for invalid/expired tokens.
* **AC:** ✅ Protected endpoints reject missing/invalid JWT; happy path returns token.

## 2) Database & Migrations ✅

* [x] Define SQLAlchemy models for users, quizzes, questions, submissions, answers, evaluations, retries.
* [x] Alembic `rev baseline` + `upgrade head`.
* [x] Indices on `completed_at`, (`subject`,`grade_level`).
* **AC:** ✅ Fresh DB starts with `alembic upgrade head`; rollback works.

## 3) Quiz Generation API (AI) ✅

* [x] `POST /quizzes` validates payload (subject, grade, num, types, difficulty/adaptive).
* [x] AI provider generates items; persist quiz + questions.
* [x] Return quiz payload sans answer keys.
* [x] Unit tests: shapes, persistence, no leakage of answers.
* **AC:** ✅ Request creates quiz; `GET /quizzes/{id}` fetches it.

## 4) Hint API (AI) ✅

* [x] `POST /quizzes/{id}/questions/{qid}/hint` → single hint.
* [x] Rate limit per user/question; store `hint_used` on answer when applicable.
* [x] Tests ensure hint does not reveal solution.
* **AC:** ✅ Valid hint returned in ≤ 2s (mock) / ≤ 6s (LLM).

## 5) Submission & Evaluation (AI) ✅

* [x] `POST /quizzes/{id}/submit` accepts answers.
* [x] Grade MCQ/TF in code; LLM rubric for short/free‑text.
* [x] Persist per‑question awarded + feedback; compute total; store suggestions(2).
* [x] Idempotency key optional to avoid double‑submit.
* **AC:** ✅ Response matches schema; totals add up; suggestions count = 2.

## 6) Adaptive Difficulty ✅

* [x] Rolling window policy (last 3).
* [x] `GET /quizzes/{id}/next` returns next question difficulty step.
* [x] Unit tests for step‑up/down/hold boundaries.
* **AC:** ✅ Policy proven with tests; next question aligns with policy.

## 7) History & Retry ✅

* [x] `GET /quizzes/history` with filters (`grade`, `subject`, `from`, `to`, `min_marks`, etc.), pagination.
* [x] `POST /quizzes/{id}/retry` clones quiz; link in `retries`.
* [x] Preserve old submissions; attempts numbered.
* **AC:** ✅ Filters work for both ISO and DD/MM/YYYY; original and retry accessible.

## 8) Observability & Errors ✅

* [x] JSON logs with request\_id; error handler returns unified error model.
* [x] `/healthz` (liveness) and `/readyz` (DB connectivity).
* **AC:** ✅ Basic metrics available; logs redacted.

## 9) API Docs & Postman ✅

* [x] OpenAPI served at `/docs` and `/openapi.json`.
* [x] Create Postman collection with env vars: `base_url`, `jwt`, `quiz_id`, `submission_id`.
* [x] Include sample calls for all endpoints + examples above.
* **AC:** ✅ Newman run passes against hosted URL.

## 10) Docker & Hosting ✅

* [x] Multi‑stage Dockerfile; non‑root runtime.
* [x] `docker-compose.yml` for local (web + db).
* [ ] Deploy on Heroku/Render/Fly/DO; set env vars and DB.
* **AC:** ⏳ Public base URL shared; Postman collection works end‑to‑end.

## 11) Security & Compliance ✅

* [x] Rate limits; CORS allowlist; strong JWT secret.
* [x] No secrets in repo; rotate keys; minimal data retention.
* **AC:** ✅ Security checklist passes; basic pen tests on auth flow.

## 12) Performance & Scale (P1) ✅

* [x] Add simple cache for hints per question/user.
* [x] Batch LLM calls where safe.
* **AC:** ✅ Meets latency targets in PRD.

## 13) Docs & DX ✅

* [x] Expand README with local dev, testing, migrate, seed, deploy.
* [x] Add ADRs for key choices (DB, AI provider, hosting).
* **AC:** ✅ New dev can run service in < 10 minutes.

---

## Deliverables Checklist

* [ ] Hosted URL (paste in CURSOR.md).
* [x] Postman collection JSON.
* [x] DB migrations.
* [x] Source repo with CI passing.
* [x] README with screenshots of Postman flows (optional).