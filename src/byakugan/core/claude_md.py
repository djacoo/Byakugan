"""Generate the root CLAUDE.md entry point — v0.3 format.

Sections: Workflow, GitFlow, Project Memory, Active Guidelines, Project Context, Privacy.
Skills from .byakugan/skills/ are embedded directly.
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path

from byakugan.core.config import ByakuganConfig
from byakugan.core.adapter import template_display_name

CLAUDE_MD_FILE = "CLAUDE.md"
BYAKUGAN_MARKER = "<!-- byakugan:managed -->"


def _load_skill(name: str, project_root: Path) -> str:
    """Load a skill file from .byakugan/skills/ or fall back to bundled."""
    local = project_root / ".byakugan" / "skills" / name
    if local.exists():
        return local.read_text(encoding="utf-8").strip()
    # Fall back to bundled
    try:
        return resources.files("byakugan.skills").joinpath(name).read_text(encoding="utf-8").strip()
    except Exception:
        return ""


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

    gitflow_content = _load_skill("gitflow-workflow.md", project_root)
    model_content = _load_skill("model-selection.md", project_root)

    lines: list[str] = [
        BYAKUGAN_MARKER,
        "# Byakugan — Active Guidelines",
        "",
        "> This project uses Byakugan for persistent guidelines and memory.",
        "> **You must follow these instructions on every tool use, without exception.**",
        "",

        # ── Workflow ──
        "## Workflow",
        "",
        "Follow the superpowers skill chain for all non-trivial work:",
        "1. `using-superpowers` → establishes skill usage",
        "2. `brainstorming` → explore intent, requirements, design",
        "3. `writing-plans` → create implementation plan",
        "4. `subagent-driven-development` or `executing-plans` → implement",
        "5. `finishing-a-development-branch` → integrate work",
        "",
    ]

    # Model selection (embedded)
    if model_content:
        lines += [model_content, ""]

    # ── GitFlow ──
    lines += ["## GitFlow", ""]
    if gitflow_content:
        lines += [gitflow_content, ""]

    # ── Project Memory ──
    lines += [
        "## Project Memory",
        "",
        "This project accumulates knowledge in `.byakugan/byakugan.db`.",
        "The hook queries it automatically and surfaces the most relevant context.",
        "",
        "**Store memories proactively** when:",
        "- The user corrects your output or approach",
        "- A project decision is made",
        "- The user expresses a preference or constraint",
        "- You discover a codebase pattern or convention",
        "",
        "```",
        'byakugan remember "correction: never do X — instead Y because Z"',
        'byakugan remember "decision: we chose X over Y because Z"',
        'byakugan remember "preference: always X when Y"',
        'byakugan remember "pattern: in this codebase, X means Y"',
        "```",
        "",
        "**Session handoff** — save context for the next session:",
        "```",
        'byakugan handoff "Working on auth refactor, need to finish JWT validation"',
        "```",
        "",
        "**Apply remembered context as hard constraints.** When the hook surfaces",
        "`[CORRECTION]`, `[PREFERENCE]`, `[DECISION]`, or `[PATTERN]` entries,",
        "treat them as binding — do not override without explicit user instruction.",
        "",
        "**Manage memories:**",
        "```",
        "byakugan memories list          # see all stored memories",
        "byakugan memories search X      # find memories about X",
        "byakugan memories forget <id>   # delete a memory",
        "byakugan memories prune         # remove stale low-value memories",
        "byakugan session list           # see session summaries",
        "byakugan session save           # manually compress current session",
        "```",
        "",
    ]

    # ── Active Guidelines ──
    lines += ["## Active Guidelines", ""]

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
        "When the `[byakugan:...]` hook fires, **read every file listed under**",
        "**`READ before proceeding`** before executing the operation.",
        "",
    ]

    # ── Project Context ──
    lines += ["## Project Context", ""]

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

    # ── Privacy ──
    lines += [
        "",
        "## Privacy — Hard Rules",
        "",
        "**Never commit these files/directories:**",
        "- `.byakugan/` — guidelines, memory DB, config",
        "- `CLAUDE.md` — generated entry point",
        "- `.claude/settings.local.json` — hook config",
        "- `.claude/remember/` — Claude Code internal memory",
        "- `.remember/` — session memory",
        "- `docs/superpowers/` — AI tooling specs/plans",
        "- `*.db` — database files",
        "",
        "The GitFlow skill checks staged files before every commit and aborts",
        "if any privacy-protected path is staged.",
        "",
        "---",
        "",
        "*Managed by Byakugan v0.3. Do not edit manually — run `byakugan update` to refresh.*",
        "",
    ]

    return "\n".join(lines)


def write(config: ByakuganConfig, project_root: Path) -> Path:
    """Write CLAUDE.md to project root."""
    content = generate(config, project_root)
    path = project_root / CLAUDE_MD_FILE
    path.write_text(content, encoding="utf-8")
    return path


def is_managed(project_root: Path) -> bool:
    """Check if the existing CLAUDE.md was generated by Byakugan."""
    path = project_root / CLAUDE_MD_FILE
    if not path.exists():
        return False
    return BYAKUGAN_MARKER in path.read_text(encoding="utf-8")
