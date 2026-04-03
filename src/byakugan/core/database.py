"""Unified SQLite database for Byakugan v0.3.

Single file: .byakugan/byakugan.db
Tables: memories, session_events, session_summaries, session_handoffs
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_FILE = "byakugan.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at       TEXT    NOT NULL,
    type             TEXT    NOT NULL,
    content          TEXT    NOT NULL,
    context          TEXT,
    tags             TEXT,
    importance       INTEGER NOT NULL DEFAULT 3,
    last_surfaced_at TEXT,
    surface_count    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS session_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT    NOT NULL,
    captured_at         TEXT    NOT NULL,
    tool_name           TEXT    NOT NULL,
    file_path           TEXT,
    tool_input_snapshot TEXT
);

CREATE TABLE IF NOT EXISTS session_summaries (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT    NOT NULL,
    period              TEXT    NOT NULL,
    created_at          TEXT    NOT NULL,
    content             TEXT    NOT NULL,
    source_event_count  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS session_handoffs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT    NOT NULL,
    content     TEXT    NOT NULL,
    branch      TEXT,
    active      INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_memories_type       ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memories_surfaced   ON memories(last_surfaced_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_session      ON session_events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_captured     ON session_events(captured_at);
CREATE INDEX IF NOT EXISTS idx_summaries_period    ON session_summaries(period, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_handoffs_active     ON session_handoffs(active);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(db_path: Path) -> None:
    """Create the database and all tables. Idempotent."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = _connect(db_path)
    conn.executescript(SCHEMA)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.close()


def get_tables(db_path: Path) -> list[str]:
    """Return list of table names in the database."""
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def migrate_from_legacy(old_db_path: Path, new_db_path: Path) -> bool:
    """Migrate memories from legacy memory.db to new byakugan.db. Returns True if migration was performed."""
    if not old_db_path.exists():
        return False
    init_db(new_db_path)
    old_conn = sqlite3.connect(str(old_db_path))
    new_conn = _connect(new_db_path)
    rows = old_conn.execute(
        "SELECT created_at, type, content, context, tags, importance, "
        "last_surfaced_at, surface_count FROM memories"
    ).fetchall()
    for row in rows:
        new_conn.execute(
            "INSERT INTO memories (created_at, type, content, context, tags, "
            "importance, last_surfaced_at, surface_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            row,
        )
    new_conn.commit()
    new_conn.close()
    old_conn.close()
    old_db_path.rename(old_db_path.with_suffix(".db.bak"))
    return True


def record_event(db_path: Path, session_id: str, tool_name: str, file_path: str | None = None, tool_input_snapshot: str | None = None) -> None:
    """Append a raw tool-use event to session_events."""
    conn = _connect(db_path)
    conn.execute(
        "INSERT INTO session_events (session_id, captured_at, tool_name, file_path, tool_input_snapshot) "
        "VALUES (?, ?, ?, ?, ?)",
        (session_id, _now_iso(), tool_name, file_path, tool_input_snapshot),
    )
    conn.commit()
    conn.close()


def get_pending_event_count(db_path: Path) -> int:
    """Count events not yet compressed into summaries."""
    conn = _connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM session_events").fetchone()[0]
    conn.close()
    return count


def get_pending_events(db_path: Path, limit: int = 200) -> list[dict]:
    """Return pending events as dicts, oldest first."""
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT id, session_id, captured_at, tool_name, file_path, tool_input_snapshot "
        "FROM session_events ORDER BY id ASC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_handoff(db_path: Path, content: str, branch: str | None = None) -> None:
    """Save a handoff note, deactivating any previous active handoff."""
    conn = _connect(db_path)
    conn.execute("UPDATE session_handoffs SET active = 0 WHERE active = 1")
    conn.execute(
        "INSERT INTO session_handoffs (created_at, content, branch, active) VALUES (?, ?, ?, 1)",
        (_now_iso(), content, branch),
    )
    conn.commit()
    conn.close()


def get_active_handoff(db_path: Path) -> dict | None:
    """Return the active handoff note, or None."""
    conn = _connect(db_path)
    row = conn.execute(
        "SELECT id, created_at, content, branch FROM session_handoffs WHERE active = 1 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_summary(db_path: Path, session_id: str, period: str, content: str, source_event_count: int = 0) -> None:
    """Save a compressed session summary."""
    conn = _connect(db_path)
    conn.execute(
        "INSERT INTO session_summaries (session_id, period, created_at, content, source_event_count) "
        "VALUES (?, ?, ?, ?, ?)",
        (session_id, period, _now_iso(), content, source_event_count),
    )
    conn.commit()
    conn.close()


def get_summaries(db_path: Path, period: str | None = None, limit: int = 50) -> list[dict]:
    """Return session summaries, optionally filtered by period."""
    conn = _connect(db_path)
    if period:
        rows = conn.execute(
            "SELECT id, session_id, period, created_at, content, source_event_count "
            "FROM session_summaries WHERE period = ? ORDER BY created_at DESC LIMIT ?",
            (period, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, session_id, period, created_at, content, source_event_count "
            "FROM session_summaries ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_events_by_ids(db_path: Path, event_ids: list[int]) -> None:
    """Delete session events by their IDs (after compression)."""
    if not event_ids:
        return
    conn = _connect(db_path)
    placeholders = ",".join("?" for _ in event_ids)
    conn.execute(f"DELETE FROM session_events WHERE id IN ({placeholders})", event_ids)
    conn.commit()
    conn.close()
