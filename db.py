"""
STREAM — Database connection layer for Neon PostgreSQL.
Provides a connection pool and query helpers for the FastAPI app.
"""

import os
import json
from pathlib import Path
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# Load .env from data_ingestion/ directory
_env_path = Path(__file__).resolve().parent / "data_ingestion" / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

DB_URL = os.environ.get("NEON_DATABASE_URL")
if not DB_URL:
    raise SystemExit("Missing NEON_DATABASE_URL environment variable")

# ── Connection pool ─────────────────────────────
pool = ConnectionPool(
    conninfo=DB_URL,
    min_size=2,
    max_size=10,
    kwargs={"row_factory": dict_row},
)


@contextmanager
def get_db():
    """Get a DB connection from the pool (dict-row cursor)."""
    with pool.connection() as conn:
        yield conn


def fetch_all(sql: str, params=None) -> list[dict]:
    """Execute a query and return all rows as dicts."""
    with get_db() as conn:
        cur = conn.execute(sql, params or ())
        return cur.fetchall()


def fetch_one(sql: str, params=None) -> dict | None:
    """Execute a query and return a single row as dict."""
    with get_db() as conn:
        cur = conn.execute(sql, params or ())
        return cur.fetchone()


def execute(sql: str, params=None):
    """Execute a write query (INSERT/UPDATE/DELETE)."""
    with get_db() as conn:
        conn.execute(sql, params or ())
        conn.commit()


def execute_returning(sql: str, params=None) -> dict | None:
    """Execute a write query with RETURNING and return the row."""
    with get_db() as conn:
        cur = conn.execute(sql, params or ())
        row = cur.fetchone()
        conn.commit()
        return row
