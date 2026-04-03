"""Tests for superpowers detection."""
from __future__ import annotations

import json
from pathlib import Path

from byakugan.core.superpowers import is_superpowers_installed


def test_detects_superpowers_when_hook_present(tmp_path: Path):
    settings = {
        "hooks": {
            "SessionStart": [{
                "matcher": "startup|clear|compact",
                "hooks": [{"type": "command", "command": "some-superpowers-hook"}]
            }]
        }
    }
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(settings))
    assert is_superpowers_installed(settings_path) is True


def test_not_detected_when_no_hooks(tmp_path: Path):
    settings = {"permissions": {}}
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(settings))
    assert is_superpowers_installed(settings_path) is False


def test_not_detected_when_file_missing(tmp_path: Path):
    settings_path = tmp_path / "settings.json"
    assert is_superpowers_installed(settings_path) is False


def test_not_detected_when_no_session_start_hook(tmp_path: Path):
    settings = {
        "hooks": {
            "PreToolUse": [{
                "matcher": "Edit",
                "hooks": [{"type": "command", "command": "some-command"}]
            }]
        }
    }
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(settings))
    assert is_superpowers_installed(settings_path) is False
