"""Vercel serverless entry — mounts the FastAPI app.

NOTE: Vercel's filesystem is ephemeral. For real persistence point
DATABASE_URL at a managed PostgreSQL (Neon / Supabase) in project env vars.
"""

from app.main import app  # noqa: F401
