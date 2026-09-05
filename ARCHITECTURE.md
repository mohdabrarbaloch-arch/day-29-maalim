# Maalim (معلم) — Verified Home-Tutor Marketplace

## The Problem
In Pakistan, parents find home tutors through word of mouth, mosque notice boards, or Facebook groups. There is no verification — anyone can claim to be "Sir from Punjab University", charge a month in advance, and vanish. Meanwhile, qualified tutors struggle to find students without a middleman (academies take 40–50% commission). Maalim fixes both sides: parents get **verified, reviewed tutors** with a structured booking flow, and tutors get **direct clients with zero commission**.

## System Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                            Browser (SPA)                            │
│  index.html · style.css · api.js · app.js  (mobile-first, dark)     │
└──────────────────────────────────────┬───────────────────────────────┘
                │ HTTPS / JSON
┌──────────────────────────────▼───────────────────────────────────────┐
│                        FastAPI (Python 3.11)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ /auth      │ │ /tutors    │ │ /bookings  │ │ /reviews /admin  │  │
│  │ register   │ │ list/search│ │ request    │ │ create (only     │  │
│  │ login (RL) │ │ filter     │ │ accept     │ │ completed)       │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
│  Middleware: JWT bearer · role guard · SlowAPI rate limits · CORS   │
│  Services:  security.py (hash/JWT) · deps.py (current_user scoping) │
└──────────────────────────────┬───────────────────────────────────────┘
                │ SQLAlchemy 2.0 ORM
┌──────────────────────────────▼───────────────────────────────────────┐
│  PostgreSQL 16 (prod/docker) · SQLite WAL (dev/test fallback)       │
│  users · tutor_profiles · bookings · reviews                        │
│  (SQLite → /tmp for Vercel serverless)                              │
└──────────────────────────────────────────────────────────────────────┘
```

## Tech Stack
| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI 0.115 | Async-ready, typed, auto OpenAPI docs |
| ORM | SQLAlchemy 2.0 | Clean models, easy SQLite→Postgres swap |
| Validation | Pydantic v2 | Schema-level input validation |
| Auth | JWT (HS256, 24h) + bcrypt(12) | Stateless + industry-standard hashing |
| Rate limit | SlowAPI | Login/register brute-force protection |
| DB | PostgreSQL 16 / SQLite WAL | prod + dev parity via DATABASE_URL |
| Frontend | Vanilla JS SPA | Zero build step, mobile-first, dark UI |
| Deploy | Docker · Vercel (`api/index.py`) | Local + serverless-ready |

## Roles
- **parent** — browse verified tutors, filter by class/subject/area/fee, request bookings, review completed bookings.
- **tutor** — create profile (subjects, classes, areas, fee PKR/hr, bio, qualification), accept/reject booking requests, mark complete; dashboard of upcoming/complete sessions.
- **admin** — verify (or reject) tutor profiles, suspend users, platform stats (tutors verified/pending, bookings by status, revenue-watch = sum of completed booking fees).

## Data Model
- **users**: id, email, full_name, phone, password_hash, role (parent|tutor|admin), is_active, is_suspended, created_at.
- **tutor_profiles**: id, user_id (1:1, role=tutor), headline, bio, qualification, institution, experience_years, subjects (JSON array), classes (JSON array), areas (JSON array), fee_per_hour (PKR), is_verified (bool), verified_at, admin_note, is_visible.
- **bookings**: id, tutor_id, parent_id, student_name, student_class, subject, area, fee_per_hour (snapshot at booking time), status (pending|accepted|rejected|completed|cancelled), schedule_note, created_at, decided_at.
- **reviews**: id, booking_id (unique), tutor_id, parent_id, rating (1–5), comment, created_at.

## Booking Lifecycle
```
parent → POST /bookings            (status=pending)
  tutor → POST /bookings/{id}/accept   → accepted   (or /reject → rejected)
  tutor → POST /bookings/{id}/complete → completed
  parent → POST /reviews               (only on a completed booking, once)
  either side may cancel while pending/accepted → cancelled
```

## Rules Engine (enforced in service + tests)
- Only **verified, visible, non-suspended tutors** appear in public tutor list; a tutor's own profile is editable regardless.
- Only a **tutor** may accept/reject/complete their own booking (404 for foreign bookings).
- A booking is reviewable **only by its parent** and **only after status=completed**; one review per booking (unique constraint → 409).
- Rating clamp 1–5; review auto-updates tutor's average rating + review_count.
- Suspended users cannot log in (403 at login).
- Admin cannot verify an unsubmitted profile; rejection requires an admin_note shown to the tutor.

## Security
- Secrets only in `.env` (SECRET_KEY, DATABASE_URL, CORS_ORIGINS); `.env.example` documents every var.
- bcrypt(12) password hashing; JWT 24h expiry; SlowAPI rate limits on auth routes.
- Scoped queries: a user only ever sees their own bookings/profiles; foreign resources return **404** (no existence leak).
- CORS allow-list from env; security headers via middleware.
- Input validation via Pydantic (email format, fee bounds 50–50,000 PKR, class 1–12, subject whitelist length caps).

## Scaling Notes
- **Stateless API** → horizontal scale behind a load balancer; JWT keeps sessions server-free.
- **DB**: SQLite (dev) → Postgres (prod) via `DATABASE_URL` only; add `indexes` on tutor_profiles(is_verified), bookings(tutor_id,status), bookings(parent_id,status) for the hot list/dashboard queries.
- **Serverless (Vercel)**: FastAPI app exposed via `api/index.py`; SQLite is ephemeral on Vercel — point `DATABASE_URL` at a managed Postgres (Neon/Supabase) for real persistence.
- **Search**: at scale, move subject/area filters to trigram indexes or Postgres full-text; cache top-rated tutor list for 60s.
- **Payments**: fee field is informational now; Stripe/PayFast escrow architecture fits between `accepted → completed` later.

## Local Run
```bash
cp .env.example .env
uvicorn app.main:app --reload          # http://localhost:8000
pytest -q                              # 40+ tests
ruff check . && black --check .
```
