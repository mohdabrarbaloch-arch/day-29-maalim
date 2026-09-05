# Maalim (معلم)

**Verified home-tutor marketplace for Pakistan** — parents find background-verified tutors for their children, request home sessions, and read honest reviews from real parents. No more word-of-mouth roulette.

![Python](https://img.shields.io/badge/Python-3.11-3776AB) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red) ![License](https://img.shields.io/badge/License-MIT-green) ![Tests](https://img.shields.io/badge/tests-44%20passing-brightgreen)

> **The problem:** In Pakistan, families find tutors through Facebook groups and word of mouth. Anyone can claim a degree, take a month's fee in advance, and disappear. Genuine tutors meanwhile lose 40–50% of their income to academies that act as middlemen. **Maalim** gives parents verified tutors with real reviews, and gives tutors direct clients — zero commission.

---

## ✨ Features

### For Parents
- 🔍 **Search & filter tutors** — by subject, area, class, fee range, and free-text search
- 🏅 **Verified-only marketplace** — every visible tutor is admin-approved with documents checked
- 📅 **One-tap booking** — request a home session with student name, class, subject & area
- ⭐ **Review completed sessions** — one honest review per booking, feeding a live tutor rating
- 🚫 **Cancel anytime** while a booking is pending/accepted

### For Tutors
- 🧑‍🏫 **Profile builder** — headline, bio, qualification, subjects, classes, areas, fee/hour
- 🔔 **Booking inbox** — accept / reject / complete requests; status-driven dashboard
- 🏷️ **Zero commission** — parents pay you directly; Maalim stays free for tutors
- 📝 **Admin notes** — if verification is rejected, the reason is shown to you

### For Admins
- ✅ **Verify / reject tutors** with an internal note shown to the tutor
- 🛡️ **Suspend users** — suspended accounts can't log in and their profile leaves public search
- 📊 **Platform stats** — users, verified/pending tutors, bookings, completed-session GMV in PKR

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.115 · Python 3.11 |
| ORM | SQLAlchemy 2.0 (SQLite dev / PostgreSQL 16 prod) |
| Validation | Pydantic v2 |
| Auth | JWT (HS256, 24h) · bcrypt(12) · SlowAPI rate limits |
| Frontend | Vanilla JS SPA — mobile-first dark UI, zero build step |
| Infra | Docker · docker-compose · Vercel-ready (`api/index.py`) |

## 🚀 Live Demo
*Deployment pending — the repo is Vercel-ready. Connect your Vercel account and run:*
```bash
vercel --prod   # then set DATABASE_URL (Neon/Supabase Postgres) in project env
```

## 🖼 Screenshots
*Screenshots will be added on first deploy — see `docs/` for local run instructions and the demo accounts below.*

## 📦 Local Install

```bash
git clone https://github.com/mohdabrarbaloch-arch/day-29-maalim
cd day-29-maalim
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # defaults work for local dev
python scripts/seed.py      # demo data + accounts
uvicorn app.main:app --reload
# open http://localhost:8000
```

### Docker
```bash
docker compose up --build   # app + PostgreSQL 16
# then run the seed inside the app container:
docker compose exec app python scripts/seed.py
```

## 🧪 Tests

```bash
pytest -q          # 44 tests — auth, tutor search/filter, booking lifecycle, reviews, admin guards, rate limits
ruff check .       # lint clean
black --check .    # format clean
```

## 👤 Demo Accounts (from seed)

| Role | Email | Password |
|---|---|---|
| Admin | `admin@maalim.pk` | `admin12345` |
| Parent | `fatima@example.com` | `parent1234` |
| Tutor (verified) | `sir.bilal@example.com` | `tutor1234` |
| Tutor (pending) | `tutor.pending@example.com` | `tutor1234` |

## 📁 Project Structure

```
project-day-29-maalim/
├── app/
│   ├── main.py            # FastAPI entrypoint + middleware + static mount
│   ├── config.py          # env-driven settings
│   ├── database.py        # engine/session (SQLite ↔ Postgres via DATABASE_URL)
│   ├── security.py        # bcrypt + JWT
│   ├── deps.py            # current-user + role guards
│   ├── models.py          # User, TutorProfile, Booking, Review
│   ├── schemas.py         # Pydantic v2 DTOs + validators
│   └── routers/           # auth, tutors, bookings, reviews, admin
├── static/                # SPA (index.html, style.css, api.js, app.js)
├── scripts/seed.py        # demo data
├── tests/                 # 44 pytest tests
├── docs/                  # setup, usage, API reference
├── api/index.py           # Vercel serverless entry
├── Dockerfile · docker-compose.yml · vercel.json
└── .env.example
```

## 🔐 Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | dev-only | JWT signing — **must change in prod** |
| `DATABASE_URL` | `sqlite:///./maalim.db` | `postgresql://user:pass@host:5432/maalim` in prod |
| `CORS_ORIGINS` | `*` | comma-separated allow-list in prod |
| `ENVIRONMENT` | `development` | `production` in prod |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | token lifetime |
| `RATE_LIMIT_LOGIN` | `10/minute` | login throttle |
| `RATE_LIMIT_REGISTER` | `5/minute` | register throttle |

## 📄 License
MIT © ABraz Baloch
