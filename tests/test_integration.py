"""End-to-end integration test for Byakugan v0.3."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

from byakugan.core.config import ByakuganConfig, ProjectProfile, save_config, load_config, get_db_path
from byakugan.core.database import init_db, get_tables, save_handoff, get_active_handoff, record_event, DB_FILE
from byakugan.core.hooks import install_hooks, hooks_installed
from byakugan.core.memory import store
from byakugan.hook_runner import handle_session_start, handle_pre_tool, handle_post_tool


def _full_project_setup(tmp_path: Path) -> Path:
    """Set up a complete v0.3 project."""
    byakugan_dir = tmp_path / ".byakugan"
    byakugan_dir.mkdir()
    (byakugan_dir / "skills").mkdir()

    db_path = byakugan_dir / DB_FILE
    init_db(db_path)

    config = ByakuganConfig(
        version="0.3.0",
        initialized_at="2026-04-01T00:00:00+00:00",
        active_templates=[
            "languages/python.md",
            "specialized/security-check.md",
            "specialized/testing-strategy.md",
        ],
        project=ProjectProfile(name="test-app", languages=["python"], frameworks=["fastapi"]),
        superpowers_detected=True,
    )
    save_config(config, tmp_path)
    install_hooks(tmp_path)

    return tmp_path


def test_full_lifecycle(tmp_path: Path):
    root = _full_project_setup(tmp_path)
    db_path = get_db_path(root)

    # 1. Store a memory
    store(db_path, "correction: always validate JWT expiry", importance=5)

    # 2. Save a handoff
    save_handoff(db_path, "Implementing auth middleware")

    # 3. Session start should include both
    output = handle_session_start(root)
    assert "auth middleware" in output
    assert "JWT expiry" in output or "validate" in output

    # 4. Pre-tool should route security files correctly
    event = {"tool_name": "Edit", "tool_input": {"file_path": "src/auth/jwt.py"}}
    with patch("byakugan.hook_runner._get_current_branch", return_value="feature/auth"):
        pre_output = handle_pre_tool(root, event)
    assert "security" in pre_output.lower()
    assert "feature/auth" in pre_output

    # 5. Post-tool should record event
    handle_post_tool(root, event, session_id="test-session")
    from byakugan.core.database import get_pending_event_count
    assert get_pending_event_count(db_path) == 1

    # 6. Hooks should all be installed
    assert hooks_installed(root) is True

    # 7. DB should have all 4 core tables
    tables = set(get_tables(db_path))
    assert {"memories", "session_events", "session_summaries", "session_handoffs"}.issubset(tables)
