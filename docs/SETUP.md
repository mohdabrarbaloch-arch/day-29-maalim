# Maalim Setup Guide

## Prerequisites
- Python 3.11+
- (optional) Docker + Docker Compose for the Postgres setup

## Local development (SQLite — quickest)

```bash
cd project-day-29-maalim
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python scripts/seed.py        # demo accounts + sample data
uvicorn app.main:app --reload
```

Open http://localhost:8000 — the SPA is served from the same origin.
Interactive API docs: http://localhost:8000/docs

## Docker + PostgreSQL 16 (production-like)

```bash
docker compose up --build
docker compose exec app python scripts/seed.py
```

App runs at http://localhost:8000, Postgres at localhost:5432.

## Vercel deployment
1. Push the repo to GitHub.
2. Import into Vercel (framework: Other).
3. Add env vars: `SECRET_KEY`, `DATABASE_URL` (managed Postgres — **required**, filesystem is ephemeral on Vercel), `CORS_ORIGINS`, `ENVIRONMENT=production`.
4. Deploy. `vercel.json` routes everything to `api/index.py`.

## Demo accounts (after seeding)

| Role | Email | Password |
|---|---|---|
| Admin | admin@maalim.pk | admin12345 |
| Parent | fatima@example.com | parent1234 |
| Parent 2 | ahmed@example.com | parent1234 |
| Tutor verified | sir.bilal@example.com | tutor1234 |
| Tutor pending | tutor.pending@example.com | tutor1234 |
