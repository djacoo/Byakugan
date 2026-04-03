"""Superpowers detection — checks ~/.claude/settings.json for superpowers hooks."""
from __future__ import annotations

import json
from pathlib import Path

GLOBAL_SETTINGS = Path.home() / ".claude" / "settings.json"


def is_superpowers_installed(settings_path: Path | None = None) -> bool:
    """Check if superpowers is installed by looking for a SessionStart hook.

    Superpowers installs a SessionStart hook in ~/.claude/settings.json.
    We detect it by checking for any SessionStart hook entry.
    """
    path = settings_path or GLOBAL_SETTINGS
    if not path.exists():
        return False

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return False

    hooks = data.get("hooks", {})
    session_start = hooks.get("SessionStart", [])
    return len(session_start) > 0
