"""Shared test fixtures for Byakugan tests."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project directory with .byakugan/ structure."""
    byakugan_dir = tmp_path / ".byakugan"
    byakugan_dir.mkdir()
    (byakugan_dir / "skills").mkdir()
    (tmp_path / ".claude").mkdir()
    return tmp_path


@pytest.fixture
def tmp_db(tmp_project: Path) -> Path:
    """Return path to a fresh byakugan.db (not yet initialized)."""
    return tmp_project / ".byakugan" / "byakugan.db"


@pytest.fixture
def old_memory_db(tmp_project: Path) -> Path:
    """Create a legacy memory.db with v0.2 schema and sample data."""
    db_path = tmp_project / ".byakugan" / "memory.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE memories (
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
        CREATE TABLE sessions (
            id          TEXT PRIMARY KEY,
            started_at  TEXT NOT NULL,
            ended_at    TEXT,
            summary     TEXT
        );
        INSERT INTO memories (created_at, type, content, importance)
        VALUES ('2026-03-01T00:00:00+00:00', 'correction', 'never use mocks for DB tests', 4);
        INSERT INTO memories (created_at, type, content, importance)
        VALUES ('2026-03-15T00:00:00+00:00', 'decision', 'use FastAPI over Flask', 3);
    """)
    conn.close()
    return db_path
