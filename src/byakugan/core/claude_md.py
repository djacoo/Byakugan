"""Generate and update the root CLAUDE.md entry point."""
from __future__ import annotations

from pathlib import Path

from byakugan.core.config import ByakuganConfig
from byakugan.core.adapter import template_display_name

CLAUDE_MD_FILE = "CLAUDE.md"
BYAKUGAN_MARKER = "<!-- byakugan:managed -->"


def generate(config: ByakuganConfig, project_root: Path) -> str:
    """Generate the full CLAUDE.md content."""
    profile = config.project
    active = config.active_templates

    by_category: dict[str, list[str]] = {
        "Languages": [],
        "Project Type": [],
        "Specialized": [],
    }
    for t in active:
        if t.startswith("languages/"):
            by_category["Languages"].append(t)
        elif t.startswith("project-types/"):
            by_category["Project Type"].append(t)
        elif t.startswith("specialized/"):
            by_category["Specialized"].append(t)

    lines: list[str] = [
        BYAKUGAN_MARKER,
        "# Byakugan — Active Guidelines",
        "",
        "> This project operates under Byakugan. Read the relevant guideline **before**",
        "> writing code, making architectural decisions, or reviewing changes.",
        "> Hooks will reference the exact files to consult. Act on every reference.",
        "",
        "## Active Guidelines",
        "",
    ]

    for category, templates in by_category.items():
        if not templates:
            continue
        lines.append(f"### {category}")
        lines.append("")
        lines.append("| File | Purpose |")
        lines.append("|------|---------|")
        for t in templates:
            path = f".byakugan/{t}"
            name = template_display_name(t)
            lines.append(f"| [`{path}`]({path}) | {name} |")
        lines.append("")

    lines += [
        "## How to Use",
        "",
        "1. **Before writing or editing code** — when a hook fires, it tells you",
        "   exactly which guideline section to consult. Read it. Apply it.",
        "2. **Before architectural decisions** — check the relevant project-type",
        "   and specialized guidelines. The `Before Starting` sections are checklists.",
        "3. **Definition of Done** — every guideline ends with one. Use it.",
        "4. **When in doubt** — read `.byakugan/` first, then act.",
        "",
        "## Memory System",
        "",
        "This project has accumulated knowledge at `.byakugan/memory.db`.",
        "The hook system queries it automatically and surfaces relevant context.",
        "",
        "**Store new knowledge whenever you learn something meaningful:**",
        "",
        "```",
        'byakugan remember "correction: do not X, instead Y — reason"',
        'byakugan remember "preference: user always wants X when doing Y"',
        'byakugan remember "decision: we use X for Y because Z"',
        'byakugan remember "pattern: when X, always do Y"',
        'byakugan remember "note: anything else worth keeping"',
        "```",
        "",
        "Memory types: `correction` · `preference` · `decision` · `pattern` · `note`",
        "",
        "Store a memory when:",
        "- The user corrects your approach or output.",
        "- A project-specific architectural decision is made.",
        "- A recurring preference or constraint is expressed.",
        "- You discover a pattern specific to this codebase.",
        "",
        "## Project Context",
        "",
    ]

    def row(label: str, value: str | None) -> None:
        if value:
            lines.append(f"- **{label}**: {value}")

    row("Project", profile.name)
    row("Languages", ", ".join(profile.languages) if profile.languages else None)
    row("Frameworks", ", ".join(profile.frameworks) if profile.frameworks else None)
    row("Package manager", profile.package_manager)
    row("Test runner", profile.test_runner)
    row("Linter", profile.linter)
    row("Formatter", profile.formatter)

    version_parts = []
    if profile.python_version:
        version_parts.append(f"Python {profile.python_version}")
    if profile.node_version:
        version_parts.append(f"Node {profile.node_version}")
    if version_parts:
        lines.append(f"- **Runtime**: {', '.join(version_parts)}")

    row("Database", profile.database)
    row("Deployment", profile.deployment)
    if profile.context:
        lines.append(f"- **Notes**: {profile.context}")

    lines += [
        "",
        "---",
        "",
        "*Managed by Byakugan. Do not edit manually.*",
        f"*Run `byakugan update` to refresh after template changes.*",
        "",
    ]

    return "\n".join(lines)


def write(config: ByakuganConfig, project_root: Path) -> Path:
    content = generate(config, project_root)
    path = project_root / CLAUDE_MD_FILE
    path.write_text(content, encoding="utf-8")
    return path


def is_managed(project_root: Path) -> bool:
    path = project_root / CLAUDE_MD_FILE
    if not path.exists():
        return False
    return BYAKUGAN_MARKER in path.read_text(encoding="utf-8")
