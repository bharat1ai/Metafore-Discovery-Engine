"""Tiny sqlite3 helpers for the local demo data store.

One DB file at backend/data/demo.db. We open a fresh connection per call
because:
  - SQLite is fast enough for this demo
  - It avoids the "SQLite objects created in a thread can only be used in
    that same thread" issue with FastAPI's worker pool
  - All operations here are short reads / one-shot seeds

Used by:
  - seed_db.py          (creates schema + inserts demo data on startup)
  - main.py /api/data/* (read-only queries powering the dashboard)
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable

DB_PATH = Path(__file__).resolve().parent / "data" / "demo.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query(sql: str, params: Iterable[Any] = ()) -> list[dict]:
    """Run a SELECT and return rows as a list of dicts."""
    conn = _connect()
    try:
        rows = conn.execute(sql, list(params)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def execute(sql: str, params: Iterable[Any] = ()) -> None:
    conn = _connect()
    try:
        conn.execute(sql, list(params))
        conn.commit()
    finally:
        conn.close()


def executescript(sql: str) -> None:
    """Run a multi-statement SQL script (CREATE/INSERT batches)."""
    conn = _connect()
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def has_table(name: str) -> bool:
    rows = query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    )
    return len(rows) > 0


def row_count(table: str) -> int:
    """Cheap COUNT(*). `table` must be a trusted constant — not user input."""
    if not table.replace("_", "").isalnum():
        raise ValueError(f"Refusing to count untrusted table name: {table!r}")
    rows = query(f"SELECT COUNT(*) AS n FROM {table}")
    return rows[0]["n"] if rows else 0
