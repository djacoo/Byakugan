"""Adapt bundled templates to a specific project's profile."""
from __future__ import annotations

from importlib import resources
from pathlib import Path

from byakugan.core.config import ProjectProfile

CONTEXT_MARKER_START = "<!-- byakugan:context:start -->"
CONTEXT_MARKER_END = "<!-- byakugan:context:end -->"

COMMANDS_MARKER_START = "<!-- byakugan:commands:start -->"
COMMANDS_MARKER_END = "<!-- byakugan:commands:end -->"


def read_bundled_template(relative_path: str) -> str:
    """Read a template from the bundled package data."""
    ref = resources.files("byakugan") / "templates" / relative_path
    return ref.read_text(encoding="utf-8")


def list_bundled_templates() -> dict[str, list[str]]:
    """Return all available templates grouped by category."""
    result: dict[str, list[str]] = {}
    for category in ("languages", "project-types", "specialized"):
        ref = resources.files("byakugan") / "templates" / category
        try:
            result[category] = sorted(
                p.name for p in ref.iterdir() if p.name.endswith(".md")
            )
        except Exception:
            result[category] = []
    return result


def build_context_block(profile: ProjectProfile) -> str:
    """Build the project-context header injected into each adapted template."""
    lines = [
        CONTEXT_MARKER_START,
        "## Project Context (Byakugan)",
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
    row("Type checker", profile.type_checker)

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
        lines.append("")
        lines.append(f"**Additional context**: {profile.context}")

    lines.append("")
    lines.append(CONTEXT_MARKER_END)
    lines.append("")
    return "\n".join(lines)


def build_commands_block(profile: ProjectProfile) -> str:
    """Build a quick-commands footer specific to the detected stack."""
    cmds: list[str] = []

    # Test commands
    if profile.test_runner == "pytest":
        cmds.append("- **Run tests**: `pytest` or `uv run pytest`")
    elif profile.test_runner == "cargo test":
        cmds.append("- **Run tests**: `cargo test`")
    elif profile.test_runner == "go test":
        cmds.append("- **Run tests**: `go test ./...`")
    elif profile.test_runner in ("vitest", "jest"):
        cmds.append(f"- **Run tests**: `{profile.package_manager} run test`")
    elif profile.test_runner == "rspec":
        cmds.append("- **Run tests**: `bundle exec rspec`")
    elif profile.test_runner == "phpunit":
        cmds.append("- **Run tests**: `./vendor/bin/phpunit`")
    elif profile.test_runner == "xcodebuild test":
        cmds.append("- **Run tests**: `xcodebuild test -scheme <scheme> -destination 'platform=iOS Simulator,...'`")

    # Format commands
    if profile.formatter == "black" and profile.linter == "ruff":
        cmds.append("- **Format + lint**: `black . && ruff check --fix .`")
    elif profile.formatter == "black":
        cmds.append("- **Format**: `black .`")
    elif profile.formatter == "ruff format":
        cmds.append("- **Format + lint**: `ruff format . && ruff check --fix .`")
    elif profile.formatter == "prettier":
        cmds.append(f"- **Format**: `{profile.package_manager} run format` or `prettier --write .`")
    elif profile.formatter == "rubocop":
        cmds.append("- **Format + lint**: `bundle exec rubocop -A`")
    elif profile.formatter == "rustfmt":
        cmds.append("- **Format**: `cargo fmt`")

    # Type check
    if profile.type_checker == "mypy":
        cmds.append("- **Type check**: `mypy src/`")
    elif profile.type_checker == "pyright":
        cmds.append("- **Type check**: `pyright`")

    # Install deps
    if profile.package_manager == "uv":
        cmds.append("- **Install deps**: `uv sync`")
    elif profile.package_manager == "poetry":
        cmds.append("- **Install deps**: `poetry install`")
    elif profile.package_manager == "cargo":
        cmds.append("- **Build**: `cargo build`")
    elif profile.package_manager == "go mod":
        cmds.append("- **Tidy deps**: `go mod tidy`")
    elif profile.package_manager in ("npm", "yarn", "pnpm", "bun"):
        cmds.append(f"- **Install deps**: `{profile.package_manager} install`")
    elif profile.package_manager == "bundler":
        cmds.append("- **Install deps**: `bundle install`")
    elif profile.package_manager == "composer":
        cmds.append("- **Install deps**: `composer install`")

    # Lint standalone
    if profile.linter == "eslint" and profile.formatter != "biome":
        cmds.append(f"- **Lint**: `{profile.package_manager} run lint`")
    elif profile.linter == "golangci-lint":
        cmds.append("- **Lint**: `golangci-lint run`")

    if not cmds:
        return ""

    lines = [
        "",
        COMMANDS_MARKER_START,
        "## Quick Commands (This Project)",
        "",
        *cmds,
        "",
        COMMANDS_MARKER_END,
    ]
    return "\n".join(lines)


def adapt_template(relative_path: str, profile: ProjectProfile) -> str:
    """
    Read the bundled template and return an adapted version:
    - Prepends the project context block.
    - Appends the project quick-commands block.
    """
    body = read_bundled_template(relative_path)

    context_block = build_context_block(profile)
    commands_block = build_commands_block(profile)

    return context_block + "\n---\n\n" + body + commands_block


def update_adapted_template(
    existing_content: str,
    relative_path: str,
    profile: ProjectProfile,
) -> str:
    """
    Re-adapt an already-adapted template:
    - Pulls the new master template body.
    - Preserves the existing context block (user's project-specific answers).
    - Refreshes the quick-commands block.
    """
    # Extract existing context block if present
    existing_context = _extract_between_markers(
        existing_content, CONTEXT_MARKER_START, CONTEXT_MARKER_END
    )

    new_body = read_bundled_template(relative_path)
    commands_block = build_commands_block(profile)

    if existing_context:
        # Preserve the existing context block (it has user's answers)
        context_section = CONTEXT_MARKER_START + existing_context + CONTEXT_MARKER_END
    else:
        context_section = build_context_block(profile)

    return context_section + "\n\n---\n\n" + new_body + commands_block


def _extract_between_markers(content: str, start: str, end: str) -> str:
    """Return the content between two markers, including the newlines around them."""
    s = content.find(start)
    e = content.find(end)
    if s == -1 or e == -1:
        return ""
    return content[s + len(start): e]


def template_display_name(relative_path: str) -> str:
    """'languages/python.md' → 'Python (language)'"""
    stem = Path(relative_path).stem
    category = relative_path.split("/")[0]
    label = {
        "languages": "language",
        "project-types": "project type",
        "specialized": "specialized",
    }.get(category, category)
    return f"{stem.replace('-', ' ').title()} ({label})"
