"""Tests for Haiku compression pipeline."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from byakugan.core.database import init_db, record_event, get_pending_event_count, get_summaries, DB_FILE
from byakugan.core.compression import (
    should_compress,
    format_events_for_compression,
    compress_events,
    COMPRESSION_THRESHOLD,
)


def test_should_compress_below_threshold(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    for i in range(5):
        record_event(db_path, session_id="s1", tool_name="Edit", file_path=f"f{i}.py")
    assert should_compress(db_path) is False


def test_should_compress_above_threshold(tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    for i in range(COMPRESSION_THRESHOLD + 1):
        record_event(db_path, session_id="s1", tool_name="Edit", file_path=f"f{i}.py")
    assert should_compress(db_path) is True


def test_format_events_for_compression():
    events = [
        {"tool_name": "Edit", "file_path": "src/auth.py", "captured_at": "2026-04-01T10:00:00+00:00",
         "tool_input_snapshot": None},
        {"tool_name": "Bash", "file_path": None, "captured_at": "2026-04-01T10:01:00+00:00",
         "tool_input_snapshot": '{"command": "pytest"}'},
    ]
    text = format_events_for_compression(events)
    assert "Edit" in text
    assert "auth.py" in text
    assert "pytest" in text


@patch("byakugan.core.compression._call_haiku")
def test_compress_events_stores_summary(mock_haiku, tmp_path: Path):
    db_path = tmp_path / DB_FILE
    init_db(db_path)
    for i in range(COMPRESSION_THRESHOLD + 1):
        record_event(db_path, session_id="s1", tool_name="Edit", file_path=f"f{i}.py")

    mock_haiku.return_value = "Edited 51 Python files in the src directory."
    compress_events(db_path)

    assert get_pending_event_count(db_path) == 0
    summaries = get_summaries(db_path, period="hourly")
    assert len(summaries) == 1
    assert "51 Python files" in summaries[0]["content"]
