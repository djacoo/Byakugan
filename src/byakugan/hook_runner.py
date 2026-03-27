"""
Hook runner — called by Claude Code on every PreToolUse event.

Reads JSON from stdin, determines context, queries memory,
and outputs a smart guideline reference to stdout.

Output is injected into Claude's context before it acts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _find_byakugan_root() -> Path | None:
    from byakugan.core.config import find_byakugan_root
    return find_byakugan_root()


def _get_language_from_path(file_path: str) -> str | None:
    ext_map = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".swift": "swift",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".css": "css",
        ".scss": "css",
        ".sass": "css",
    }
    ext = Path(file_path).suffix.lower()
    return ext_map.get(ext)


def _template_section_hint(template_path: str, operation: str) -> str:
    """Return the most relevant section name to consult given the operation."""
    if "security" in template_path:
        return "§Input Validation Checklist + §OWASP Top 10"
    if "code-review" in template_path:
        return "§What to Review + §Severity Classification"
    if "testing" in template_path:
        return "§Unit Testing Standards + §Definition of Done"
    if "database" in template_path:
        return "§Schema Design + §Query Standards"
    if operation in ("Edit", "Write", "MultiEdit"):
        return "§Code Standards + §Hard Rules + §Definition of Done"
    if operation == "Bash":
        return "§How to Approach Any Task"
    return "§Non-Negotiable Rules"


def _build_output(
    root: Path,
    tool_name: str,
    file_path: str | None,
    active_templates: list[str],
    memories: list,
) -> str:
    language = _get_language_from_path(file_path) if file_path else None

    # Determine which templates are most relevant
    relevant: list[str] = []

    for t in active_templates:
        stem = Path(t).stem

        # Language match
        if language and stem == language:
            relevant.append(t)
            continue
        if language and stem in ("typescript", "javascript") and language in ("typescript", "javascript"):
            relevant.append(t)
            continue

        # Always include active project-type and specialized templates
        if t.startswith("project-types/") or t.startswith("specialized/"):
            # Filter out templates clearly unrelated to a non-code operation
            if tool_name == "Bash" and "review" in stem:
                continue
            relevant.append(t)

    if not relevant:
        relevant = active_templates[:3]

    # Build the reference lines
    lines = ["[Byakugan]"]

    if file_path:
        rel = Path(file_path).name
        action = {"Edit": "Editing", "Write": "Writing", "MultiEdit": "Editing", "Bash": "Running command in"}.get(tool_name, "Working on")
        lang_note = f" ({language})" if language else ""
        lines.append(f"{action} `{rel}`{lang_note} — consult before proceeding:")
    else:
        lines.append("Consult before proceeding:")

    for t in relevant[:4]:  # cap at 4 to keep output concise
        byakugan_path = f".byakugan/{t}"
        hint = _template_section_hint(t, tool_name)
        lines.append(f"  → {byakugan_path}  {hint}")

    if memories:
        lines.append("Memory:")
        for m in memories[:3]:
            short = m.content[:100] + ("…" if len(m.content) > 100 else "")
            lines.append(f"  • [{m.type}] {short}")

    return "\n".join(lines)


def run() -> None:
    """Entry point called by the Claude Code hook."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        event = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    tool_name: str = event.get("tool_name", "")
    tool_input: dict = event.get("tool_input", {})

    # Extract the file being operated on
    file_path: str | None = (
        tool_input.get("file_path")
        or tool_input.get("path")
        or None
    )

    root = _find_byakugan_root()
    if root is None:
        sys.exit(0)

    # Load config
    try:
        from byakugan.core.config import load_config, get_memory_path
        config = load_config(root)
        active_templates = config.active_templates
    except Exception:
        sys.exit(0)

    # Query memory
    memories = []
    try:
        from byakugan.core import memory as mem
        db_path = get_memory_path(root)
        language = _get_language_from_path(file_path) if file_path else None
        memories = mem.query_relevant(
            db_path,
            language=language,
            file_path=file_path,
            limit=3,
        )
    except Exception:
        pass

    output = _build_output(root, tool_name, file_path, active_templates, memories)
    print(output)
    sys.exit(0)
