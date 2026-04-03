"""Tests for the 3-hook configuration system."""
from __future__ import annotations

import json
from pathlib import Path

from byakugan.core.hooks import install_hooks, uninstall_hooks, hooks_installed, HOOK_CONFIG


def test_hook_config_has_three_events():
    assert "SessionStart" in HOOK_CONFIG
    assert "PreToolUse" in HOOK_CONFIG
    assert "PostToolUse" in HOOK_CONFIG


def test_post_tool_hook_is_async():
    post_hooks = HOOK_CONFIG["PostToolUse"][0]["hooks"]
    assert post_hooks[0].get("async") is True


def test_install_hooks_writes_all_three(tmp_path: Path):
    install_hooks(tmp_path)
    settings = json.loads((tmp_path / ".claude" / "settings.local.json").read_text())
    hooks = settings["hooks"]
    assert "SessionStart" in hooks
    assert "PreToolUse" in hooks
    assert "PostToolUse" in hooks


def test_install_hooks_preserves_existing_non_byakugan_hooks(tmp_path: Path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    existing = {
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": "some-other-tool"}]
            }]
        }
    }
    (claude_dir / "settings.local.json").write_text(json.dumps(existing))

    install_hooks(tmp_path)
    settings = json.loads((claude_dir / "settings.local.json").read_text())
    pre_tool = settings["hooks"]["PreToolUse"]
    commands = [h["hooks"][0]["command"] for h in pre_tool]
    assert "some-other-tool" in commands
    assert any("byakugan" in c for c in commands)


def test_uninstall_hooks_removes_all_byakugan(tmp_path: Path):
    install_hooks(tmp_path)
    uninstall_hooks(tmp_path)
    settings = json.loads((tmp_path / ".claude" / "settings.local.json").read_text())
    hooks = settings.get("hooks", {})
    for entries in hooks.values():
        for entry in entries:
            for h in entry.get("hooks", []):
                assert "byakugan" not in h.get("command", "")


def test_hooks_installed_detects_all_three(tmp_path: Path):
    assert hooks_installed(tmp_path) is False
    install_hooks(tmp_path)
    assert hooks_installed(tmp_path) is True
