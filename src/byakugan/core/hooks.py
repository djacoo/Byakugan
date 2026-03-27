"""Manage Claude Code hook configuration in .claude/settings.local.json."""
from __future__ import annotations

import json
import shutil
from pathlib import Path


SETTINGS_PATH = Path(".claude") / "settings.local.json"

HOOK_COMMAND = "byakugan hook"

HOOK_CONFIG = {
    "PreToolUse": [
        {
            "matcher": "Edit|Write|MultiEdit|Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": HOOK_COMMAND,
                }
            ],
        }
    ]
}


def install_hooks(project_root: Path) -> None:
    """Merge Byakugan hooks into .claude/settings.local.json."""
    settings_file = project_root / SETTINGS_PATH
    settings_file.parent.mkdir(parents=True, exist_ok=True)

    existing: dict = {}
    if settings_file.exists():
        try:
            existing = json.loads(settings_file.read_text())
        except json.JSONDecodeError:
            existing = {}

    hooks = existing.setdefault("hooks", {})

    for event, entries in HOOK_CONFIG.items():
        existing_entries = hooks.setdefault(event, [])
        # Remove any stale Byakugan hook entries before re-adding
        existing_entries[:] = [
            e for e in existing_entries
            if not _is_byakugan_hook(e)
        ]
        existing_entries.extend(entries)

    settings_file.write_text(json.dumps(existing, indent=2) + "\n")


def uninstall_hooks(project_root: Path) -> None:
    """Remove Byakugan hooks from .claude/settings.local.json."""
    settings_file = project_root / SETTINGS_PATH
    if not settings_file.exists():
        return

    try:
        existing = json.loads(settings_file.read_text())
    except json.JSONDecodeError:
        return

    hooks = existing.get("hooks", {})
    for event in list(hooks.keys()):
        hooks[event] = [e for e in hooks[event] if not _is_byakugan_hook(e)]
        if not hooks[event]:
            del hooks[event]

    if not hooks:
        existing.pop("hooks", None)

    settings_file.write_text(json.dumps(existing, indent=2) + "\n")


def hooks_installed(project_root: Path) -> bool:
    settings_file = project_root / SETTINGS_PATH
    if not settings_file.exists():
        return False
    try:
        data = json.loads(settings_file.read_text())
    except json.JSONDecodeError:
        return False
    for entries in data.get("hooks", {}).values():
        for entry in entries:
            if _is_byakugan_hook(entry):
                return True
    return False


def byakugan_in_path() -> bool:
    return shutil.which("byakugan") is not None


def _is_byakugan_hook(entry: dict) -> bool:
    for hook in entry.get("hooks", []):
        if HOOK_COMMAND in hook.get("command", ""):
            return True
    return False
