"""
Unified hook engine — handles SessionStart, PreToolUse, PostToolUse.

SessionStart: injects context (handoff, summaries, memories) ≤800 tokens
PreToolUse:   routes guidelines, warns on protected branches ≤300 tokens
PostToolUse:  captures events to DB asynchronously (0 tokens to context)
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


# ── Session constants ─────────────────────────────────────────────────────────

SESSION_TTL = 3600
_TMP = Path(os.environ.get("TMPDIR", "/tmp"))
SESSION_DIR = _TMP / "byakugan"


# ── Suppression rules (unchanged from v0.2) ──────────────────────────────────

SUPPRESS_EXTENSIONS = {
    ".md", ".txt", ".rst", ".toml", ".json", ".lock",
    ".env", ".gitignore", ".gitattributes", ".editorconfig",
    ".prettierrc", ".eslintrc", ".nvmrc", ".python-version",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf",
}

YAML_INFRA_PATTERNS = frozenset({
    "docker-compose", "docker_compose",
    "kubernetes", "k8s", "helm",
    "deployment", "service", "ingress", "configmap", "statefulset",
})

SUPPRESS_PATH_PARTS = frozenset({
    "node_modules", ".venv", "venv", "__pycache__", ".git",
    "dist", "build", "target", ".byakugan", ".tox",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
})

TRIVIAL_BASH_WORDS = frozenset({
    "ls", "cat", "echo", "pwd", "cd", "cp", "mv", "mkdir", "touch",
    "which", "env", "set", "export", "source", "head", "tail", "wc",
    "grep", "find", "less", "more", "man", "history", "clear", "date",
})


# ── File-path routing (unchanged from v0.2) ──────────────────────────────────

PATH_ROUTING: list[tuple[list[str], str]] = [
    (["auth", "login", "password", "passwd", "token", "jwt", "oauth",
      "secret", "crypto", "cipher", "session", "permission", "role", "acl"],
     "specialized/security-check.md"),
    (["test", "spec", "_test.", ".test.", "tests/", "__tests__"],
     "specialized/testing-strategy.md"),
    (["migration", "alembic", "flyway", "schema.sql", "seed", "fixture",
      "knex", "prisma/"],
     "specialized/database-design.md"),
    (["model", "entity", "repository", "dao", "models/", "entities/"],
     "specialized/database-design.md"),
    (["route", "handler", "controller", "endpoint", "views/", "api/v"],
     "specialized/api-design.md"),
    (["dockerfile", "docker-compose", ".tf", ".k8s", "kubernetes",
      ".github/workflow", "pipeline", "helm", "ansible", "deploy"],
     "specialized/devops-infrastructure.md"),
    (["refactor", "cleanup", "reorganize", "restructure"],
     "specialized/refactoring.md"),
    (["perf", "benchmark", "profile", "optimize", "cache"],
     "specialized/performance-optimization.md"),
]

HIGH_RISK_STEMS = frozenset({
    "auth", "login", "password", "passwd", "token", "jwt", "oauth",
    "secret", "crypto", "cipher", "session", "permission", "role",
})

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

_HINTS: dict[str, dict[str, str]] = {
    "security-check": {
        "Edit": "§Input Validation + §OWASP Top 10",
        "Write": "§Input Validation + §OWASP Top 10",
        "MultiEdit": "§Input Validation + §OWASP Top 10",
        "Bash": "§Authentication",
        "default": "§OWASP Top 10",
    },
    "testing-strategy": {
        "Edit": "§Unit Testing Standards + §Definition of Done",
        "Write": "§Test Structure",
        "Bash": "§Test Runner",
        "default": "§Unit Testing Standards",
    },
    "database-design": {
        "Edit": "§Schema Design + §Query Standards",
        "Write": "§Schema Design",
        "Bash": "§Migration Standards",
        "default": "§Schema Design",
    },
    "api-design": {
        "Edit": "§Endpoint Design + §Response Format",
        "Write": "§Endpoint Design",
        "default": "§Endpoint Design",
    },
    "gitflow-workflow": {
        "Bash": "§Commit Messages + §Branch Naming",
        "default": "§Branch Strategy",
    },
    "devops-infrastructure": {
        "Edit": "§Container Standards + §Secrets",
        "Write": "§Container Standards",
        "Bash": "§Deployment Checklist",
        "default": "§Security",
    },
    "refactoring": {
        "Edit": "§Refactoring Rules + §Definition of Done",
        "default": "§Refactoring Rules",
    },
    "performance-optimization": {
        "Edit": "§Profile First + §Common Patterns",
        "default": "§Profile First",
    },
    "debugging": {"Bash": "§Debugging Process", "default": "§Debugging Process"},
    "code-review": {"default": "§What to Review + §Severity"},
    "code-simplification": {"Edit": "§Simplification Rules", "default": "§Simplification Rules"},
    "ai-usage-policy": {"default": "§Usage Rules"},
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


# ── Git helpers ──────────────────────────────────────────────────────────────

def _get_current_branch() -> str | None:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


# ── Session management (unchanged logic) ─────────────────────────────────────

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


# ── Analysis helpers (unchanged from v0.2) ───────────────────────────────────

def _should_suppress(file_path: str | None, tool_name: str, tool_input: dict) -> bool:
    if file_path:
        p = Path(file_path)
        suffix = p.suffix.lower()
        if suffix in SUPPRESS_EXTENSIONS:
            return True
        if suffix in (".yaml", ".yml"):
            lower_path = file_path.lower()
            is_infra = (
                any(pat in lower_path for pat in YAML_INFRA_PATTERNS)
                or ".github/workflows" in lower_path
                or "/.github/" in lower_path
            )
            if not is_infra:
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
    tool_name: str, tool_input: dict, file_path: str | None, active_templates: list[str],
) -> tuple[list[str], bool]:
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
            for t in active_templates:
                if t.startswith("project-types/"):
                    add(t)
                    break
    else:
        for t in _route_by_file(file_path, active):
            add(t)
        lang = _get_language(file_path)
        if lang_t := _language_template(lang, active):
            add(lang_t)
        if not result:
            for t in active_templates:
                if t.startswith("project-types/"):
                    add(t)

    return result[:4], high_risk


# ── SESSION-START handler ────────────────────────────────────────────────────

def handle_session_start(root: Path) -> str:
    """Generate session-start context. Budget: ≤800 tokens."""
    from byakugan.core.config import load_config, get_db_path
    from byakugan.core.database import get_active_handoff, get_summaries
    from byakugan.core.memory import get_high_importance

    db_path = get_db_path(root)
    lines: list[str] = ["[byakugan] session context"]

    # 1. Active handoff (always included, ≤150 tokens)
    handoff = get_active_handoff(db_path)
    if handoff:
        branch_note = f" (branch: {handoff['branch']})" if handoff.get("branch") else ""
        lines.append(f"  handoff{branch_note}: {handoff['content']}")

    # 2. Today's hourly summaries (≤300 tokens)
    summaries = get_summaries(db_path, period="hourly", limit=3)
    if summaries:
        lines.append("  recent activity:")
        for s in summaries:
            preview = s["content"][:120]
            lines.append(f"    - {preview}")

    # 3. High-importance memories (≤200 tokens)
    memories = get_high_importance(db_path, min_importance=4, limit=5)
    if memories:
        lines.append("  key memories:")
        for m in memories:
            icon = m.type.upper()
            short = m.content[:80]
            lines.append(f"    [{icon}] {short}")

    # 4. Weekly digest (≤150 tokens, dropped first if over budget)
    weekly = get_summaries(db_path, period="weekly", limit=1)
    if weekly:
        lines.append(f"  weekly digest: {weekly[0]['content'][:120]}")

    # Trigger background compression if needed
    try:
        from byakugan.core.compression import should_compress, spawn_background_compression
        if should_compress(db_path):
            spawn_background_compression(db_path)
    except Exception:
        pass

    # Branch info
    branch = _get_current_branch()
    if branch:
        from byakugan.core.gitflow import is_protected_branch
        warning = " — PROTECTED, do not commit directly" if is_protected_branch(branch) else ""
        lines.append(f"  branch: {branch}{warning}")

    return "\n".join(lines)


# ── PRE-TOOL handler ────────────────────────────────────────────────────────

def handle_pre_tool(root: Path, event: dict) -> str | None:
    """Generate pre-tool guidance. Budget: ≤300 tokens."""
    from byakugan.core.config import load_config, get_db_path

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path") or None

    if _should_suppress(file_path, tool_name, tool_input):
        return None

    try:
        config = load_config(root)
        active_templates = config.active_templates
    except Exception:
        return None

    session = _load_session(root)

    # Query memories
    memories: list = []
    try:
        from byakugan.core import memory as mem
        db_path = get_db_path(root)
        language = _get_language(file_path)
        keywords: list[str] = []
        if file_path:
            p = Path(file_path)
            keywords = [p.stem] + [part for part in p.parts[-3:-1] if len(part) > 2]
        memories = mem.query_relevant(
            db_path, language=language, file_path=file_path,
            keywords=keywords or None, operation=tool_name, limit=3,
        )
        if memories:
            mem.update_surfaced(db_path, [m.id for m in memories])
    except Exception:
        pass

    # Build output
    relevant, high_risk = _select_relevant(tool_name, tool_input, file_path, active_templates)

    if not relevant and not memories:
        return None

    shown_set: set[str] = set(session.get("shown", []))
    lines: list[str] = []

    # Branch header
    branch = _get_current_branch()
    branch_info = ""
    if branch:
        from byakugan.core.gitflow import is_protected_branch
        if is_protected_branch(branch):
            branch_info = f" — on protected branch [{branch}]"
        else:
            branch_info = f" [{branch}]"

    # Header
    if file_path:
        name = Path(file_path).name
        lang = _get_language(file_path)
        lang_note = f" ({lang})" if lang else ""
        action = {"Edit": "edit", "Write": "write", "MultiEdit": "edit", "Bash": "bash"}.get(tool_name, tool_name.lower())
        risk_flag = " HIGH-RISK" if high_risk else ""
        lines.append(f"[byakugan:{action}] {name}{lang_note}{risk_flag}{branch_info}")
    elif tool_name == "Bash":
        cmd_preview = (tool_input.get("command") or "")[:60]
        lines.append(f"[byakugan:bash] `{cmd_preview}`{branch_info}")
    else:
        lines.append(f"[byakugan:{tool_name.lower()}]{branch_info}")

    def _force_show(t: str) -> bool:
        return high_risk and "security" in t

    new_templates = [t for t in relevant if t not in shown_set or _force_show(t)]
    already_shown = [t for t in relevant if t in shown_set and not _force_show(t)]

    if new_templates:
        lines.append("  READ before proceeding:")
        for t in new_templates:
            hint = _section_hint(t, tool_name)
            lines.append(f"    .byakugan/{t}  ({hint})")

    if already_shown and session.get("call_count", 0) > 0:
        stems = " . ".join(Path(t).stem for t in already_shown)
        lines.append(f"  guidelines also apply: {stems}")

    if memories:
        lines.append("  remembered context:")
        for m in memories[:3]:
            short = m.content[:90] + ("..." if len(m.content) > 90 else "")
            icon = m.type.upper()
            lines.append(f"    [{icon}] {short}")

    # Update session
    shown_set.update(relevant)
    session["shown"] = list(shown_set)
    session["call_count"] = session.get("call_count", 0) + 1
    _save_session(root, session)

    return "\n".join(lines) if lines else None


# ── POST-TOOL handler ───────────────────────────────────────────────────────

def handle_post_tool(root: Path, event: dict, session_id: str | None = None) -> None:
    """Capture tool event to DB. Async — no output."""
    from byakugan.core.config import get_db_path
    from byakugan.core.database import record_event

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path") or None

    # Truncate tool_input for snapshot
    snapshot = None
    if tool_input:
        snap = {}
        if file_path:
            snap["file_path"] = file_path
        if cmd := tool_input.get("command"):
            snap["command"] = cmd[:200]
        if snap:
            snapshot = json.dumps(snap)

    db_path = get_db_path(root)
    sid = session_id or _project_hash(root)

    try:
        record_event(db_path, session_id=sid, tool_name=tool_name,
                     file_path=file_path, tool_input_snapshot=snapshot)
    except Exception:
        pass

    # Check compression threshold
    try:
        from byakugan.core.compression import should_compress, spawn_background_compression
        if should_compress(db_path):
            spawn_background_compression(db_path)
    except Exception:
        pass


# ── Entry point ──────────────────────────────────────────────────────────────

def run(hook_type: str | None = None) -> None:
    """Unified entry point for all hook types."""
    try:
        raw = sys.stdin.read()
    except OSError:
        raw = ""

    # Find project root
    try:
        from byakugan.core.config import find_byakugan_root
        root = find_byakugan_root()
        if root is None:
            sys.exit(0)
    except Exception:
        sys.exit(0)

    if hook_type == "session-start":
        output = handle_session_start(root)
        if output:
            print(output)

    elif hook_type == "pre-tool":
        if not raw.strip():
            sys.exit(0)
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            sys.exit(0)
        output = handle_pre_tool(root, event)
        if output:
            print(output)

    elif hook_type == "post-tool":
        if not raw.strip():
            sys.exit(0)
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            sys.exit(0)
        handle_post_tool(root, event)

    else:
        # Fallback: treat as pre-tool for backward compat
        if not raw.strip():
            sys.exit(0)
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            sys.exit(0)
        output = handle_pre_tool(root, event)
        if output:
            print(output)

    sys.exit(0)
