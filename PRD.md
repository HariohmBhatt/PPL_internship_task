# PRD.md

## Title

AI‑Powered Quiz Microservice (Auth, Quiz Management, AI Evaluation, Score Tracking)

**Owner:** Hariohm Bhatt
**Date:** 2025‑08‑09 (IST)
**Version:** 1.0 (Initial)

---

## 1) Summary

Build and host a containerized microservice that issues JWTs, generates quizzes with AI, evaluates answers (MCQ + short/free‑text) with AI, adapts difficulty in real‑time, and tracks scores/history with filters. Expose a clean REST API, provide DB migrations, a Postman collection, and a hosted URL.

---

## 2) Goals & Non‑Goals

**Goals**

* 🔐 Mock login → signed JWT; gate all quiz endpoints with token.
* 🧩 Quiz lifecycle: generate → attempt → submit → evaluate → store → query history.
* 🧠 AI features: per‑question hint on demand; 2 improvement tips post‑submission; adaptive difficulty per quiz session.
* 🗃️ Durable storage for quizzes, questions, submissions, answers, and evaluations; provide SQL migrations.
* 🚀 Docker image and deployment to a third‑party host; publish base URL and Postman collection.

**Non‑Goals**

* Full web UI (out of scope; this is API‑only).
* Proctoring / anti‑cheat.
* Advanced user management/roles beyond a simple “user” scope.

---

## 3) Success Metrics (MVP)

* P0: End‑to‑end happy path works via Postman on the hosted URL.
* P0: Latency p95 < 800 ms for non‑AI endpoints; p95 < 4 s for AI‑graded questions (LLM calls).
* P1: ≥ 95% successful JWT validations; zero secrets in logs; 100% migration reproducibility.

---

## 4) Personas & Key Journeys

**Test‑taker**

* Logs in (mock) → receives JWT → requests a quiz (subject/grade/size) → answers → asks for a hint on Q3 → submits → sees score + 2 tips → can retry → views past attempts filtered by date/subject.

**Client App (consumer)**

* Integrates JWT flow; calls generation/evaluation/history endpoints; renders hints, tracks attempt IDs, and paginates history.

---

## 5) Scope & Assumptions

* Single tenant; multi‑user via JWT subject.
* English content initially; model provider is configurable (OpenAI/Local).
* Time zones stored in UTC; date filters accept ISO 8601 and DD/MM/YYYY for convenience.
* AI responses are guardrailed and may be cached for idempotency.

---

## 6) Functional Requirements

### 6.1 Authentication

* **POST /auth/login** (mock): accepts any username/password; returns a signed JWT (HS256) with `sub`, `exp`, and `scope:["user"]`.
* All `/quizzes/*` endpoints require `Authorization: Bearer <JWT>`; tokens expire in 24h (configurable).

### 6.2 Quiz Generation (AI)

* **POST /quizzes**: create a new quiz and persist it.
* Accepts subject, grade, number of questions, difficulty (easy/medium/hard/adaptive), topics (optional), question types (`mcq`, `true_false`, `short_answer`).
* When `difficulty=adaptive`, the service computes next‑question difficulty on the fly during attempts.

**Sample request**

```json
{
  "subject": "mathematics",
  "grade_level": "8",
  "num_questions": 8,
  "difficulty": "adaptive",
  "topics": ["fractions", "decimals"],
  "question_types": ["mcq", "short_answer"],
  "standard": "CBSE-Grade-8"
}
```

**Sample response**

```json
{
  "quiz_id": "qz_01HXYZ",
  "subject": "mathematics",
  "grade_level": "8",
  "difficulty_mode": "adaptive",
  "questions": [
    {
      "question_id": "q_001",
      "type": "mcq",
      "prompt": "Which is greater: 3/4 or 5/8?",
      "options": ["3/4", "5/8", "equal", "cannot say"],
      "topic": "fractions",
      "difficulty": "medium"
    }
  ],
  "created_at": "2025-08-09T10:45:00Z"
}
```

### 6.3 Hint Generation (AI)

* **POST /quizzes/{quiz\_id}/questions/{question\_id}/hint**
* Returns a single actionable hint. Prevents leaking the direct answer. Rate‑limited per question/user.

**Response (example)**

```json
{
  "question_id": "q_001",
  "hint": "Convert both fractions to have the same denominator before comparing."
}
```

### 6.4 Submission & Evaluation (AI)

* **POST /quizzes/{quiz\_id}/submit**: accepts answers, evaluates, persists, returns breakdown + 2 improvement tips.
* MCQ/TF: rule‑based. Short/free‑text: LLM rubric with deterministic system prompt and reference answer.

**Sample request**

```json
{
  "answers": [
    {"question_id": "q_001", "response": "3/4"},
    {"question_id": "q_002", "response": "Because decimals…"}
  ],
  "request_suggestions": true
}
```

**Sample response**

```json
{
  "submission_id": "sbm_01ABC",
  "total_score": 7.5,
  "max_score": 10,
  "per_question": [
    {
      "question_id": "q_001",
      "correct": true,
      "awarded": 1,
      "max": 1,
      "feedback": "Correct — you compared common denominators."
    },
    {
      "question_id": "q_002",
      "correct": false,
      "awarded": 0.5,
      "max": 2,
      "feedback": "Partially correct; include place‑value justification."
    }
  ],
  "suggestions": [
    "Practice converting between fractions and decimals.",
    "Slow down on explanation steps; show one worked example."
  ],
  "completed_at": "2025-08-09T10:58:11Z"
}
```

### 6.5 History & Filters

* **GET /quizzes/history**: filters by `grade`, `subject`, `min_marks`, `max_marks`, `from`, `to`, `completedDate`, `limit`, `offset`.
* Accept both ISO (`2024-09-01`) and `DD/MM/YYYY` (`01/09/2024`); service normalizes to UTC for queries.

**Example**: `/quizzes/history?subject=math&grade=8&from=01/09/2024&to=09/09/2024&min_marks=6`

### 6.6 Retry flow

* **POST /quizzes/{quiz\_id}/retry** → clones original quiz (linking `retry_of`) and allows a new submission; original remains accessible.

### 6.7 Adaptive Difficulty

* Track a rolling window (last 3 answers).
* If accuracy ≥ 0.66 → step difficulty up one level; if ≤ 0.33 → step down; else hold.
* Start at requested base difficulty or `medium` if unspecified.
* Never drop below `easy` nor above `hard`.
* For adaptive quizzes, **GET /quizzes/{quiz\_id}/next** returns the next item based on the current state.

---

## 7) API Overview

```
POST   /auth/login
POST   /quizzes
GET    /quizzes/{quiz_id}
POST   /quizzes/{quiz_id}/questions/{question_id}/hint
POST   /quizzes/{quiz_id}/submit
GET    /quizzes/history
POST   /quizzes/{quiz_id}/retry
GET    /quizzes/{quiz_id}/next   (adaptive only)
```

**Auth:** Bearer JWT required for all except `/auth/login`.

**Error model**

```json
{"error": {"code": "BAD_REQUEST", "message": "details…", "field": "answers[1]"}}
```

Common codes: `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `RATE_LIMITED`, `VALIDATION_ERROR`.

---

## 8) Data Model (Relational)

**users**(id, username, created\_at)

**quizzes**(id, subject, grade\_level, difficulty\_mode, created\_by, created\_at, standard)

**questions**(id, quiz\_id, type, prompt, topic, difficulty, options\_json, answer\_key\_json, points\_default)

**submissions**(id, quiz\_id, user\_id, attempt\_no, created\_at, completed\_at)

**answers**(id, submission\_id, question\_id, response\_text, selected\_option, awarded, max\_points, correct, hint\_used)

**evaluations**(id, submission\_id, total\_score, suggestions\_json, detail\_json, evaluated\_at)

**retries**(original\_quiz\_id, retry\_quiz\_id)

> JSON columns are `jsonb` (PostgreSQL). Indices on `subject`, `grade_level`, `completed_at`.

---

## 9) Non‑Functional Requirements

* **Security:** HS256 JWT; rotate secret via env; CORS allowlist; basic rate limiting; PII‑minimal logs.
* **Reliability:** Idempotent evaluation on retries; health checks `/healthz`, `/readyz`.
* **Performance:** Pagination on history; batch evaluate; optional caching of hints per question/user.
* **Observability:** Structured logs (JSON), request IDs, basic metrics (req/sec, p95, error rate).
* **Testing:** Unit (logic), integration (DB), contract (OpenAPI), e2e (Postman/newman).
* **Docs:** OpenAPI at `/docs` via FastAPI.

---

## 10) Architecture & Tech Choices (recommended)

* **Language/Framework:** Python 3.11 + FastAPI.
* **DB:** PostgreSQL 14+ (SQLAlchemy + Alembic migrations).
* **Auth:** PyJWT (HS256).
* **AI Provider abstraction:** driver interface with pluggable backends (OpenAI, local).
* **Packaging:** Dockerfile + docker‑compose for local.
* **CI:** GitHub Actions (lint, test, build, push image).
* **Hosting (MVP):** Render/Heroku/Fly.io/DO App Platform; expose base URL.

---

## 11) Migrations (example SQL excerpt)

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE quizzes (
  id UUID PRIMARY KEY,
  subject TEXT NOT NULL,
  grade_level TEXT NOT NULL,
  difficulty_mode TEXT NOT NULL,
  created_by UUID REFERENCES users(id),
  standard TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE questions (
  id UUID PRIMARY KEY,
  quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  prompt TEXT NOT NULL,
  topic TEXT,
  difficulty TEXT,
  options_json JSONB,
  answer_key_json JSONB,
  points_default REAL DEFAULT 1
);
CREATE TABLE submissions (
  id UUID PRIMARY KEY,
  quiz_id UUID REFERENCES quizzes(id),
  user_id UUID REFERENCES users(id),
  attempt_no INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);
CREATE TABLE answers (
  id UUID PRIMARY KEY,
  submission_id UUID REFERENCES submissions(id) ON DELETE CASCADE,
  question_id UUID REFERENCES questions(id),
  response_text TEXT,
  selected_option TEXT,
  awarded REAL DEFAULT 0,
  max_points REAL DEFAULT 1,
  correct BOOLEAN,
  hint_used BOOLEAN DEFAULT FALSE
);
CREATE TABLE evaluations (
  id UUID PRIMARY KEY,
  submission_id UUID UNIQUE REFERENCES submissions(id) ON DELETE CASCADE,
  total_score REAL,
  suggestions_json JSONB,
  detail_json JSONB,
  evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE retries (
  original_quiz_id UUID REFERENCES quizzes(id),
  retry_quiz_id UUID REFERENCES quizzes(id),
  PRIMARY KEY (original_quiz_id, retry_quiz_id)
);
CREATE INDEX idx_submissions_completed_at ON submissions(completed_at);
CREATE INDEX idx_quizzes_subject_grade ON quizzes(subject, grade_level);
```

---

## 12) AI Prompting (implementation notes)

* **Hints:** system prompt forbids revealing the final answer; provide one conceptual nudge.
* **Short‑answer grading:** rubric with reference answer + point allocation, require concise justification in feedback.
* **Suggestions:** produce exactly 2, specific to mistakes, each ≤ 140 chars.

---

## 13) Open Questions

* Should we store full AI prompts/responses for audit (config‑gated)?
* Per‑user mastery model across quizzes (beyond session‑level adaptive)?
* Rate limits per IP vs per user?

---


