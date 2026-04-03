"""GitFlow enforcement — staged file privacy checks."""
from __future__ import annotations

import re

PROTECTED_PATTERNS = [
    r"^\.byakugan/",
    r"^CLAUDE\.md$",
    r"^\.claude/settings\.local\.json$",
    r"^\.claude/remember/",
    r"^\.remember/",
    r"^docs/superpowers/",
    r"\.db$",
]

_COMPILED = [re.compile(p) for p in PROTECTED_PATTERNS]

PROTECTED_BRANCHES = {"main", "develop"}


def check_staged_privacy(staged_files: list[str]) -> list[str]:
    """Return list of staged files that violate privacy rules."""
    violations = []
    for f in staged_files:
        for pattern in _COMPILED:
            if pattern.search(f):
                violations.append(f)
                break
    return violations


def is_protected_branch(branch: str) -> bool:
    """Check if a branch name is protected (main, develop)."""
    return branch in PROTECTED_BRANCHES
