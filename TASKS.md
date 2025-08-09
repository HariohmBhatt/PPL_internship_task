# TASKS.md

> Detailed task plan with subtasks and acceptance criteria. Use ✅/❌ and checkboxes.

## 0) Project Bootstrap

* [ ] Create repo with layout from **CURSOR\_RULES.md**.
* [ ] Add `README.md` with local/dev/prod instructions.
* [ ] Add `.env.example` (JWT\_SECRET, DATABASE\_URL, OPENAI\_API\_KEY optional, ALLOWED\_ORIGINS).
* [ ] Configure ruff, black, mypy, pytest, pre-commit.
* **AC:** Repo boots with `uvicorn app.main:app`, health endpoints respond.

## 1) Authentication

* [ ] Implement `POST /auth/login` (mock) → issue JWT (24h).
* [ ] Add dependency to verify JWT on `/quizzes/*`.
* [ ] Add negative tests for invalid/expired tokens.
* **AC:** Protected endpoints reject missing/invalid JWT; happy path returns token.

## 2) Database & Migrations

* [ ] Define SQLAlchemy models for users, quizzes, questions, submissions, answers, evaluations, retries.
* [ ] Alembic `rev baseline` + `upgrade head`.
* [ ] Indices on `completed_at`, (`subject`,`grade_level`).
* **AC:** Fresh DB starts with `alembic upgrade head`; rollback works.

## 3) Quiz Generation API (AI)

* [ ] `POST /quizzes` validates payload (subject, grade, num, types, difficulty/adaptive).
* [ ] AI provider generates items; persist quiz + questions.
* [ ] Return quiz payload sans answer keys.
* [ ] Unit tests: shapes, persistence, no leakage of answers.
* **AC:** Request creates quiz; `GET /quizzes/{id}` fetches it.

## 4) Hint API (AI)

* [ ] `POST /quizzes/{id}/questions/{qid}/hint` → single hint.
* [ ] Rate limit per user/question; store `hint_used` on answer when applicable.
* [ ] Tests ensure hint does not reveal solution.
* **AC:** Valid hint returned in ≤ 2s (mock) / ≤ 6s (LLM).

## 5) Submission & Evaluation (AI)

* [ ] `POST /quizzes/{id}/submit` accepts answers.
* [ ] Grade MCQ/TF in code; LLM rubric for short/free‑text.
* [ ] Persist per‑question awarded + feedback; compute total; store suggestions(2).
* [ ] Idempotency key optional to avoid double‑submit.
* **AC:** Response matches schema; totals add up; suggestions count = 2.

## 6) Adaptive Difficulty

* [ ] Rolling window policy (last 3).
* [ ] `GET /quizzes/{id}/next` returns next question difficulty step.
* [ ] Unit tests for step‑up/down/hold boundaries.
* **AC:** Policy proven with tests; next question aligns with policy.

## 7) History & Retry

* [ ] `GET /quizzes/history` with filters (`grade`, `subject`, `from`, `to`, `min_marks`, etc.), pagination.
* [ ] `POST /quizzes/{id}/retry` clones quiz; link in `retries`.
* [ ] Preserve old submissions; attempts numbered.
* **AC:** Filters work for both ISO and DD/MM/YYYY; original and retry accessible.

## 8) Observability & Errors

* [ ] JSON logs with request\_id; error handler returns unified error model.
* [ ] `/healthz` (liveness) and `/readyz` (DB connectivity).
* **AC:** Basic metrics available; logs redacted.

## 9) API Docs & Postman

* [ ] OpenAPI served at `/docs` and `/openapi.json`.
* [ ] Create Postman collection with env vars: `base_url`, `jwt`, `quiz_id`, `submission_id`.
* [ ] Include sample calls for all endpoints + examples above.
* **AC:** Newman run passes against hosted URL.

## 10) Docker & Hosting

* [ ] Multi‑stage Dockerfile; non‑root runtime.
* [ ] `docker-compose.yml` for local (web + db).
* [ ] Deploy on Heroku/Render/Fly/DO; set env vars and DB.
* **AC:** Public base URL shared; Postman collection works end‑to‑end.

## 11) Security & Compliance

* [ ] Rate limits; CORS allowlist; strong JWT secret.
* [ ] No secrets in repo; rotate keys; minimal data retention.
* **AC:** Security checklist passes; basic pen tests on auth flow.

## 12) Performance & Scale (P1)

* [ ] Add simple cache for hints per question/user.
* [ ] Batch LLM calls where safe.
* **AC:** Meets latency targets in PRD.

## 13) Docs & DX

* [ ] Expand README with local dev, testing, migrate, seed, deploy.
* [ ] Add ADRs for key choices (DB, AI provider, hosting).
* **AC:** New dev can run service in < 10 minutes.

---

## Deliverables Checklist

* [ ] Hosted URL (paste in CURSOR.md).
* [ ] Postman collection JSON.
* [ ] DB migrations.
* [ ] Source repo with CI passing.
* [ ] README with screenshots of Postman flows (optional).