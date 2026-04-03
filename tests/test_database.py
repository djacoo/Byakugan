"""Tests for the unified database layer."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from byakugan.core.database import (
    init_db, get_tables, migrate_from_legacy, record_event,
    get_pending_event_count, get_pending_events, save_handoff,
    get_active_handoff, save_summary, get_summaries, delete_events_by_ids,
    DB_FILE,
)


def test_init_db_creates_all_tables(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    tables = get_tables(db_path)
    assert "memories" in tables
    assert "session_events" in tables
    assert "session_summaries" in tables
    assert "session_handoffs" in tables
    assert "sessions" not in tables


def test_init_db_is_idempotent(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    init_db(db_path)
    tables = get_tables(db_path)
    assert len(tables) == 4


def test_init_db_uses_wal_mode(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    assert mode == "wal"


def test_migrate_from_legacy_copies_memories(old_memory_db, tmp_db):
    migrate_from_legacy(old_memory_db, tmp_db)
    conn = sqlite3.connect(str(tmp_db))
    rows = conn.execute("SELECT content FROM memories ORDER BY id").fetchall()
    conn.close()
    assert len(rows) == 2
    assert rows[0][0] == "never use mocks for DB tests"
    assert rows[1][0] == "use FastAPI over Flask"


def test_migrate_from_legacy_renames_old_db(old_memory_db, tmp_db):
    migrate_from_legacy(old_memory_db, tmp_db)
    assert not old_memory_db.exists()
    assert old_memory_db.with_suffix(".db.bak").exists()


def test_migrate_from_legacy_skips_if_no_old_db(tmp_db):
    fake_old = tmp_db.parent / "memory.db"
    migrate_from_legacy(fake_old, tmp_db)
    assert not tmp_db.exists()


def test_record_event(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    record_event(db_path, session_id="s1", tool_name="Edit", file_path="src/main.py",
                 tool_input_snapshot='{"file_path": "src/main.py"}')
    assert get_pending_event_count(db_path) == 1


def test_get_pending_events(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    record_event(db_path, session_id="s1", tool_name="Edit", file_path="a.py")
    record_event(db_path, session_id="s1", tool_name="Bash", file_path=None,
                 tool_input_snapshot='{"command": "pytest"}')
    events = get_pending_events(db_path)
    assert len(events) == 2
    assert events[0]["tool_name"] == "Edit"


def test_save_handoff(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    save_handoff(db_path, "Working on auth refactor", branch="feature/auth")
    handoff = get_active_handoff(db_path)
    assert handoff is not None
    assert handoff["content"] == "Working on auth refactor"
    assert handoff["branch"] == "feature/auth"


def test_save_handoff_deactivates_previous(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    save_handoff(db_path, "First note")
    save_handoff(db_path, "Second note")
    handoff = get_active_handoff(db_path)
    assert handoff["content"] == "Second note"
    conn = sqlite3.connect(str(db_path))
    active_count = conn.execute("SELECT COUNT(*) FROM session_handoffs WHERE active = 1").fetchone()[0]
    conn.close()
    assert active_count == 1


def test_get_active_handoff_returns_none_when_empty(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    assert get_active_handoff(db_path) is None


def test_save_summary(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    save_summary(db_path, session_id="s1", period="hourly",
                 content="Edited auth module, added JWT validation", source_event_count=12)
    summaries = get_summaries(db_path, period="hourly")
    assert len(summaries) == 1
    assert summaries[0]["content"] == "Edited auth module, added JWT validation"
    assert summaries[0]["source_event_count"] == 12


def test_delete_events_by_ids(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    record_event(db_path, session_id="s1", tool_name="Edit", file_path="a.py")
    record_event(db_path, session_id="s1", tool_name="Edit", file_path="b.py")
    events = get_pending_events(db_path)
    delete_events_by_ids(db_path, [events[0]["id"]])
    assert get_pending_event_count(db_path) == 1
