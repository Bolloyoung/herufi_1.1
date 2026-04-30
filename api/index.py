"""Vercel serverless entry point.

Vercel's Python runtime detects an ASGI app exported as `app` from this file.
All requests are routed here via vercel.json.

Constraints on Vercel:
- No persistent file system  → use PostgreSQL (DATABASE_URL=postgresql+asyncpg://...)
- No background processes    → lifespan auto-creates tables on cold start
- Static files               → served by Vercel directly from /public (see vercel.json)
"""
import sys
import os

# Make the repo root importable regardless of how Vercel resolves paths.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: F401, E402 — re-exported for Vercel

__all__ = ["app"]
