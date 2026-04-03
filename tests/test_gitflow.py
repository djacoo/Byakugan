"""Tests for GitFlow privacy checks."""
from byakugan.core.gitflow import check_staged_privacy, PROTECTED_PATTERNS


def test_detects_byakugan_dir():
    staged = [".byakugan/byakugan.toml", "src/main.py"]
    violations = check_staged_privacy(staged)
    assert ".byakugan/byakugan.toml" in violations
    assert "src/main.py" not in violations


def test_detects_claude_md():
    staged = ["CLAUDE.md", "README.md"]
    violations = check_staged_privacy(staged)
    assert "CLAUDE.md" in violations
    assert "README.md" not in violations


def test_detects_settings_local():
    staged = [".claude/settings.local.json"]
    violations = check_staged_privacy(staged)
    assert ".claude/settings.local.json" in violations


def test_detects_db_files():
    staged = ["data/test.db", "src/main.py"]
    violations = check_staged_privacy(staged)
    assert "data/test.db" in violations


def test_no_violations_on_clean_files():
    staged = ["src/main.py", "tests/test_main.py", "pyproject.toml"]
    violations = check_staged_privacy(staged)
    assert violations == []
