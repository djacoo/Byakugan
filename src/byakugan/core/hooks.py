"""Manage Claude Code hook configuration in .claude/settings.local.json.

v0.3: Three hooks — SessionStart, PreToolUse, PostToolUse.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path


SETTINGS_PATH = Path(".claude") / "settings.local.json"

HOOK_COMMAND_PREFIX = "byakugan hook --type"

HOOK_CONFIG = {
    "SessionStart": [
        {
            "matcher": "startup|clear|compact",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{HOOK_COMMAND_PREFIX} session-start",
                }
            ],
        }
    ],
    "PreToolUse": [
        {
            "matcher": "Edit|Write|MultiEdit|Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{HOOK_COMMAND_PREFIX} pre-tool",
                }
            ],
        }
    ],
    "PostToolUse": [
        {
            "matcher": "Edit|Write|MultiEdit|Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{HOOK_COMMAND_PREFIX} post-tool",
                    "async": True,
                }
            ],
        }
    ],
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
        # Remove stale Byakugan entries before re-adding
        existing_entries[:] = [
            e for e in existing_entries
            if not _is_byakugan_hook(e)
        ]
        existing_entries.extend(entries)

    settings_file.write_text(json.dumps(existing, indent=2) + "\n")


def uninstall_hooks(project_root: Path) -> None:
    """Remove all Byakugan hooks from .claude/settings.local.json."""
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
    """Check if all three Byakugan hooks are present."""
    settings_file = project_root / SETTINGS_PATH
    if not settings_file.exists():
        return False
    try:
        data = json.loads(settings_file.read_text())
    except json.JSONDecodeError:
        return False

    hooks = data.get("hooks", {})
    required = {"SessionStart", "PreToolUse", "PostToolUse"}
    found = set()
    for event, entries in hooks.items():
        for entry in entries:
            if _is_byakugan_hook(entry):
                found.add(event)
    return required.issubset(found)


def byakugan_in_path() -> bool:
    """Check if byakugan CLI is available on PATH."""
    return shutil.which("byakugan") is not None


def _is_byakugan_hook(entry: dict) -> bool:
    """Check if a hook entry belongs to Byakugan."""
    for hook in entry.get("hooks", []):
        cmd = hook.get("command", "")
        if "byakugan hook" in cmd or "byakugan" in cmd.split()[0:1]:
            return True
    return False
