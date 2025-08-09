# CURSOR.md
> Working log & decisions for the Quiz Microservice. Keep terse, append‑only. Timestamps in IST.

## 2025‑08‑09 16:00 — Project Kickoff

* Created initial docs: PRD, RULES, TASKS.
* Stack chosen: FastAPI + Postgres + SQLAlchemy + Alembic.
* Hosting target: Heroku/Render (whichever provides quickest Postgres + container).
* Open items: pick AI provider (OpenAI vs mock for MVP).

## Decisions

* Store JSON blobs (`options_json`, `answer_key_json`, `suggestions_json`) in `jsonb`.
* Accept both ISO and DD/MM/YYYY; normalize to UTC.

## TODO (short)

* Scaffold FastAPI app + routers.
* Alembic initial migration.
* JWT util + dependency.
* Implement `/auth/login` and `/healthz`.

## Links

* (to add) Hosted URL: TBD
* (to add) Postman: TBD
