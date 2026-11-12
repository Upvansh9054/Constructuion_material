"""Vercel Serverless Function entrypoint for Demolition Intelligence FastAPI Backend."""
import os
import sys
import asyncio

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Import the FastAPI application instance
from app.main import app
from app.core.config import settings

# If running in Vercel serverless environment, ensure SQLite db is initialized in /tmp
if os.getenv("VERCEL") == "1":
    try:
        from app.core.database import engine, Base
        async def init_vercel_db():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        asyncio.run(init_vercel_db())
    except Exception as exc:
        print(f"Vercel DB initialization warning: {exc}")
