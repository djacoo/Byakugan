"""
Hook runner — called by Claude Code on every PreToolUse event.

Smart context injection with:
- File-path semantic routing (test files → testing-strategy, auth files → security, etc.)
- Bash command parsing (git → gitflow, pytest → testing, docker → devops, etc.)
- Session deduplication (avoid repeating the same references every call)
- Operation-aware memory scoring
- Compact, low-token output format
- Fast-path suppression for non-code files and trivial commands
- Root and config caching via session state
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path


# ── Session constants ─────────────────────────────────────────────────────────

SESSION_TTL = 600  # seconds — after this, session resets (new conversation)
_TMP = Path(os.environ.get("TMPDIR", "/tmp"))
SESSION_DIR = _TMP / "byakugan"


# ── Suppression rules ─────────────────────────────────────────────────────────

# File extensions that carry no code → skip entirely
SUPPRESS_EXTENSIONS = {
    ".md", ".txt", ".rst", ".toml", ".yaml", ".yml", ".json", ".lock",
    ".env", ".gitignore", ".gitattributes", ".editorconfig",
    ".prettierrc", ".eslintrc", ".nvmrc", ".python-version",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf",
}

# Path components that mean "internal / generated / not Claude's business"
SUPPRESS_PATH_PARTS = frozenset({
    "node_modules", ".venv", "venv", "__pycache__", ".git",
    "dist", "build", "target", ".byakugan", ".tox",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
})

# Bash first-words that are too trivial to need guidance
TRIVIAL_BASH_WORDS = frozenset({
    "ls", "cat", "echo", "pwd", "cd", "cp", "mv", "mkdir", "touch",
    "which", "env", "set", "export", "source", "head", "tail", "wc",
    "grep", "find", "less", "more", "man", "history", "clear", "date",
})


# ── File-path routing ─────────────────────────────────────────────────────────
# (patterns_in_lowercased_path, template_key)
# First match wins per template. Ordered by specificity.

PATH_ROUTING: list[tuple[list[str], str]] = [
    # Security-sensitive files — always surface, even if shown before
    (["auth", "login", "password", "passwd", "token", "jwt", "oauth",
      "secret", "crypto", "cipher", "session", "permission", "role", "acl"],
     "specialized/security-check.md"),
    # Test files
    (["test", "spec", "_test.", ".test.", "tests/", "__tests__"],
     "specialized/testing-strategy.md"),
    # Database / schema / migrations
    (["migration", "alembic", "flyway", "schema.sql", "seed", "fixture",
      "knex", "prisma/"],
     "specialized/database-design.md"),
    (["model", "entity", "repository", "dao", "models/", "entities/"],
     "specialized/database-design.md"),
    # API routes / controllers
    (["route", "handler", "controller", "endpoint", "views/", "api/v"],
     "specialized/api-design.md"),
    # Infrastructure
    (["dockerfile", "docker-compose", ".tf", ".k8s", "kubernetes",
      ".github/workflow", "pipeline", "helm", "ansible", "deploy"],
     "specialized/devops-infrastructure.md"),
    # Refactoring
    (["refactor", "cleanup", "reorganize", "restructure"],
     "specialized/refactoring.md"),
    # Performance
    (["perf", "benchmark", "profile", "optimize", "cache"],
     "specialized/performance-optimization.md"),
]

# Patterns that make the file "high-risk" — security template always shown
HIGH_RISK_STEMS = frozenset({
    "auth", "login", "password", "passwd", "token", "jwt", "oauth",
    "secret", "crypto", "cipher", "session", "permission", "role",
})


# ── Bash command routing ──────────────────────────────────────────────────────
# (substrings_in_lowercased_command, template_key)

BASH_ROUTING: list[tuple[list[str], str]] = [
    (["git commit", "git push", "git merge", "git rebase", "git tag",
      "git cherry-pick", "git stash"],
     "specialized/gitflow-workflow.md"),
    (["pytest", "cargo test", "go test", "npm test", "npx jest",
      "vitest", "bun test", "rspec", "phpunit", "xcodebuild test"],
     "specialized/testing-strategy.md"),
    (["docker", "kubectl", "terraform", "helm", "ansible", "pulumi",
      "cdk deploy", "sam deploy"],
     "specialized/devops-infrastructure.md"),
    (["psql", "mysql", "sqlite3", "alembic", "flask db", "django migrate",
      "knex migrate", "prisma migrate", "dbmate", "flyway"],
     "specialized/database-design.md"),
    (["npm audit", "pip-audit", "cargo audit", "safety check",
      "trivy", "snyk", "bandit"],
     "specialized/security-check.md"),
    (["black ", "ruff ", "prettier ", "eslint --fix", "rubocop -A",
      "cargo fmt", "gofmt", "biome format"],
     "specialized/code-simplification.md"),
]


# ── Section hints ─────────────────────────────────────────────────────────────
# Derived per template-stem × operation type

_HINTS: dict[str, dict[str, str]] = {
    "security-check": {
        "Edit":     "§Input Validation + §OWASP Top 10",
        "Write":    "§Input Validation + §OWASP Top 10",
        "MultiEdit":"§Input Validation + §OWASP Top 10",
        "Bash":     "§Authentication",
        "default":  "§OWASP Top 10",
    },
    "testing-strategy": {
        "Edit":     "§Unit Testing Standards + §Definition of Done",
        "Write":    "§Test Structure",
        "Bash":     "§Test Runner",
        "default":  "§Unit Testing Standards",
    },
    "database-design": {
        "Edit":     "§Schema Design + §Query Standards",
        "Write":    "§Schema Design",
        "Bash":     "§Migration Standards",
        "default":  "§Schema Design",
    },
    "api-design": {
        "Edit":     "§Endpoint Design + §Response Format",
        "Write":    "§Endpoint Design",
        "default":  "§Endpoint Design",
    },
    "gitflow-workflow": {
        "Bash":     "§Commit Messages + §Branch Naming",
        "default":  "§Branch Strategy",
    },
    "devops-infrastructure": {
        "Edit":     "§Container Standards + §Secrets",
        "Write":    "§Container Standards",
        "Bash":     "§Deployment Checklist",
        "default":  "§Security",
    },
    "refactoring": {
        "Edit":     "§Refactoring Rules + §Definition of Done",
        "default":  "§Refactoring Rules",
    },
    "performance-optimization": {
        "Edit":     "§Profile First + §Common Patterns",
        "default":  "§Profile First",
    },
    "debugging": {
        "Bash":     "§Debugging Process",
        "default":  "§Debugging Process",
    },
    "code-review": {
        "default":  "§What to Review + §Severity",
    },
    "code-simplification": {
        "Edit":     "§Simplification Rules",
        "default":  "§Simplification Rules",
    },
    "ai-usage-policy": {
        "default":  "§Usage Rules",
    },
}

EXT_TO_LANGUAGE: dict[str, str] = {
    ".py": "python", ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".rs": "rust", ".go": "go", ".java": "java",
    ".kt": "kotlin", ".kts": "kotlin", ".swift": "swift",
    ".rb": "ruby", ".php": "php",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".cc": "cpp",
    ".cxx": "cpp", ".hpp": "cpp",
    ".css": "css", ".scss": "css", ".sass": "css",
}


# ── Session management ────────────────────────────────────────────────────────

def _project_hash(root: Path) -> str:
    return hashlib.md5(str(root).encode()).hexdigest()[:8]


def _session_file(root: Path) -> Path:
    return SESSION_DIR / f"session-{_project_hash(root)}.json"


def _load_session(root: Path) -> dict:
    sf = _session_file(root)
    try:
        if sf.exists():
            data = json.loads(sf.read_text())
            if time.time() - data.get("ts", 0) < SESSION_TTL:
                return data
    except Exception:
        pass
    return {"ts": time.time(), "shown": [], "call_count": 0}


def _save_session(root: Path, session: dict) -> None:
    try:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        session["ts"] = time.time()
        _session_file(root).write_text(json.dumps(session))
    except Exception:
        pass


# ── Analysis helpers ──────────────────────────────────────────────────────────

def _should_suppress(file_path: str | None, tool_name: str, tool_input: dict) -> bool:
    """Return True if this operation doesn't need guidelines."""
    if file_path:
        p = Path(file_path)
        if p.suffix.lower() in SUPPRESS_EXTENSIONS:
            return True
        if SUPPRESS_PATH_PARTS.intersection(p.parts):
            return True

    if tool_name == "Bash":
        cmd = (tool_input.get("command") or "").strip()
        if not cmd:
            return True
        first = cmd.lstrip("./").split()[0] if cmd.split() else ""
        if first in TRIVIAL_BASH_WORDS:
            return True

    return False


def _is_high_risk(file_path: str | None) -> bool:
    if not file_path:
        return False
    lower = Path(file_path).name.lower()
    return any(pat in lower for pat in HIGH_RISK_STEMS)


def _get_language(file_path: str | None) -> str | None:
    if not file_path:
        return None
    return EXT_TO_LANGUAGE.get(Path(file_path).suffix.lower())


def _route_by_file(file_path: str | None, active: set[str]) -> list[str]:
    if not file_path:
        return []
    lower = file_path.lower()
    matched: list[str] = []
    seen: set[str] = set()
    for patterns, template in PATH_ROUTING:
        if template in seen or template not in active:
            continue
        if any(pat in lower for pat in patterns):
            matched.append(template)
            seen.add(template)
    return matched


def _route_by_bash(command: str, active: set[str]) -> list[str]:
    lower = command.lower()
    matched: list[str] = []
    seen: set[str] = set()
    for patterns, template in BASH_ROUTING:
        if template in seen or template not in active:
            continue
        if any(pat in lower for pat in patterns):
            matched.append(template)
            seen.add(template)
    return matched


def _language_template(language: str | None, active: set[str]) -> str | None:
    if not language:
        return None
    t = f"languages/{language}.md"
    return t if t in active else None


def _section_hint(template: str, tool_name: str) -> str:
    stem = Path(template).stem
    hints = _HINTS.get(stem)
    if hints:
        return hints.get(tool_name, hints.get("default", "§Hard Rules"))
    if template.startswith("languages/"):
        return "§Code Standards + §Hard Rules" if tool_name != "Bash" else "§How to Approach Any Task"
    if template.startswith("project-types/"):
        return "§Architecture + §Definition of Done" if tool_name != "Bash" else "§How to Approach Any Task"
    return "§Hard Rules"


def _select_relevant(
    tool_name: str,
    tool_input: dict,
    file_path: str | None,
    active_templates: list[str],
) -> tuple[list[str], bool]:
    """
    Return (relevant_templates, is_high_risk).
    Templates are ordered: path-routed first, then language, then project-types.
    """
    active = set(active_templates)
    high_risk = _is_high_risk(file_path)
    seen: set[str] = set()
    result: list[str] = []

    def add(t: str) -> None:
        if t not in seen and t in active:
            result.append(t)
            seen.add(t)

    if tool_name == "Bash":
        cmd = tool_input.get("command") or ""
        for t in _route_by_bash(cmd, active):
            add(t)
        if not result:
            # No specific match → show a project-type template as fallback
            for t in active_templates:
                if t.startswith("project-types/"):
                    add(t)
                    break
    else:
        # 1. Path-specific routing (highest priority)
        for t in _route_by_file(file_path, active):
            add(t)
        # 2. Language template
        lang = _get_language(file_path)
        if lang_t := _language_template(lang, active):
            add(lang_t)
        # 3. Fallback: project-type templates if nothing matched
        if not result:
            for t in active_templates:
                if t.startswith("project-types/"):
                    add(t)

    return result[:4], high_risk


# ── Output builder ────────────────────────────────────────────────────────────

def _build_output(
    root: Path,
    tool_name: str,
    tool_input: dict,
    file_path: str | None,
    active_templates: list[str],
    memories: list,
    session: dict,
) -> str | None:
    relevant, high_risk = _select_relevant(tool_name, tool_input, file_path, active_templates)

    if not relevant and not memories:
        return None

    shown_set: set[str] = set(session.get("shown", []))
    is_first_call = session.get("call_count", 0) == 0

    # High-risk security template: always show regardless of session state
    def _force_show(t: str) -> bool:
        return high_risk and "security" in t

    new_templates = [t for t in relevant if t not in shown_set or _force_show(t)]
    already_shown = [t for t in relevant if t in shown_set and not _force_show(t)]

    # If this is the first call or there's nothing new, decide output level
    if not new_templates and not memories:
        if already_shown:
            stems = " · ".join(Path(t).stem for t in already_shown)
            return f"[byk] {stems} — guidelines apply (already in context)"
        return None

    lines: list[str] = []

    # ── Header ──
    if file_path:
        name = Path(file_path).name
        lang = _get_language(file_path)
        lang_note = f" ({lang})" if lang else ""
        action = {"Edit": "edit", "Write": "write", "MultiEdit": "edit", "Bash": "bash"}.get(tool_name, tool_name.lower())
        risk_flag = " ⚠ HIGH-RISK" if high_risk else ""
        lines.append(f"[byk:{action}] {name}{lang_note}{risk_flag}")
    elif tool_name == "Bash":
        cmd_preview = (tool_input.get("command") or "")[:60]
        lines.append(f"[byk:bash] `{cmd_preview}`")
    else:
        lines.append(f"[byk:{tool_name.lower()}]")

    # ── New template references (full) ──
    for t in new_templates:
        hint = _section_hint(t, tool_name)
        lines.append(f"  → .byakugan/{t}  {hint}")

    # ── Already-seen templates (compact reminder) ──
    if already_shown and not is_first_call:
        stems = " · ".join(Path(t).stem for t in already_shown)
        lines.append(f"  (also: {stems})")

    # ── Memories ──
    if memories:
        for m in memories[:3]:
            short = m.content[:90] + ("…" if len(m.content) > 90 else "")
            icon = {"correction": "✗", "preference": "◇", "decision": "◆", "pattern": "◈"}.get(m.type, "·")
            lines.append(f"  {icon} [{m.type}] {short}")

    # ── Staleness reminder (if config is old) ──
    try:
        from byakugan.core.config import load_config
        cfg = load_config(root)
        last = cfg.last_updated or cfg.initialized_at
        if last:
            age = (time.time() - _parse_iso_ts(last)) / 86400
            if age > 30 and session.get("call_count", 0) % 20 == 0:
                lines.append("  [dim]Tip: run byakugan update to refresh guidelines[/dim]")
    except Exception:
        pass

    return "\n".join(lines)


def _parse_iso_ts(iso: str) -> float:
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return 0.0


# ── Entry point ───────────────────────────────────────────────────────────────

def run() -> None:
    """Entry point called by the Claude Code PreToolUse hook."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        event = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    tool_name: str = event.get("tool_name", "")
    tool_input: dict = event.get("tool_input", {})

    # Extract file path (Edit/Write/MultiEdit use file_path, some Bash inputs have path)
    file_path: str | None = tool_input.get("file_path") or tool_input.get("path") or None

    # Fast path: skip non-code operations
    if _should_suppress(file_path, tool_name, tool_input):
        sys.exit(0)

    # Find byakugan root
    try:
        from byakugan.core.config import find_byakugan_root, load_config, get_memory_path
        root = find_byakugan_root()
        if root is None:
            sys.exit(0)
    except Exception:
        sys.exit(0)

    # Load session state (contains shown-templates tracking)
    session = _load_session(root)

    # Load config (fast — TOML is small)
    try:
        config = load_config(root)
        active_templates = config.active_templates
    except Exception:
        sys.exit(0)

    # Query memory with rich operation context
    memories: list = []
    try:
        from byakugan.core import memory as mem
        db_path = get_memory_path(root)
        language = _get_language(file_path)

        # Extract keywords from file path for better memory matching
        keywords: list[str] = []
        if file_path:
            p = Path(file_path)
            keywords = [p.stem] + [part for part in p.parts[-3:-1] if len(part) > 2]

        memories = mem.query_relevant(
            db_path,
            language=language,
            file_path=file_path,
            keywords=keywords or None,
            operation=tool_name,
            limit=3,
        )

        # Record that these memories were surfaced
        if memories:
            mem.update_surfaced(db_path, [m.id for m in memories])
    except Exception:
        pass

    # Build output
    output = _build_output(root, tool_name, tool_input, file_path, active_templates, memories, session)

    # Update session state
    relevant, _ = _select_relevant(tool_name, tool_input, file_path, active_templates)
    shown_set: set[str] = set(session.get("shown", []))
    shown_set.update(relevant)
    session["shown"] = list(shown_set)
    session["call_count"] = session.get("call_count", 0) + 1
    _save_session(root, session)

    if output:
        print(output)

    sys.exit(0)
