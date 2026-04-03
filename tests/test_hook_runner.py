"""Tests for the unified hook engine."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from byakugan.core.database import init_db, save_handoff, record_event, DB_FILE
from byakugan.core.config import ByakuganConfig, ProjectProfile, save_config, get_db_path


def _setup_project(tmp_path: Path) -> Path:
    """Create a minimal initialized project for hook testing."""
    byakugan_dir = tmp_path / ".byakugan"
    byakugan_dir.mkdir(exist_ok=True)
    db_path = byakugan_dir / DB_FILE
    init_db(db_path)

    config = ByakuganConfig(
        version="0.3.0",
        initialized_at="2026-04-01T00:00:00+00:00",
        active_templates=["languages/python.md", "specialized/security-check.md"],
        project=ProjectProfile(name="test", languages=["python"]),
    )
    save_config(config, tmp_path)
    return tmp_path


def test_session_start_includes_handoff(tmp_path: Path):
    root = _setup_project(tmp_path)
    db_path = root / ".byakugan" / DB_FILE
    save_handoff(db_path, "Working on auth refactor", branch="feature/auth")

    from byakugan.hook_runner import handle_session_start
    output = handle_session_start(root)
    assert "auth refactor" in output
    assert "feature/auth" in output


def test_session_start_includes_high_importance_memories(tmp_path: Path):
    root = _setup_project(tmp_path)
    db_path = root / ".byakugan" / DB_FILE
    from byakugan.core.memory import store
    store(db_path, "correction: never use wildcard imports", importance=5)

    from byakugan.hook_runner import handle_session_start
    output = handle_session_start(root)
    assert "wildcard imports" in output


def test_pre_tool_warns_protected_branch(tmp_path: Path):
    root = _setup_project(tmp_path)
    from byakugan.hook_runner import handle_pre_tool

    event = {"tool_name": "Edit", "tool_input": {"file_path": "src/main.py"}}
    with patch("byakugan.hook_runner._get_current_branch", return_value="main"):
        output = handle_pre_tool(root, event)
    assert "main" in output
    assert "protected" in output.lower()


def test_pre_tool_routes_security_files(tmp_path: Path):
    root = _setup_project(tmp_path)
    from byakugan.hook_runner import handle_pre_tool

    event = {"tool_name": "Edit", "tool_input": {"file_path": "src/auth/login.py"}}
    with patch("byakugan.hook_runner._get_current_branch", return_value="feature/auth"):
        output = handle_pre_tool(root, event)
    assert "security" in output.lower()


def test_post_tool_records_event(tmp_path: Path):
    root = _setup_project(tmp_path)
    from byakugan.hook_runner import handle_post_tool
    from byakugan.core.database import get_pending_event_count

    db_path = root / ".byakugan" / DB_FILE
    event = {"tool_name": "Edit", "tool_input": {"file_path": "src/main.py"}}
    handle_post_tool(root, event, session_id="test-session")
    assert get_pending_event_count(db_path) == 1
