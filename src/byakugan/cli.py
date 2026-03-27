"""Byakugan — Claude Code guideline system."""
from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="byakugan",
    help="Byakugan — Claude Code guideline and memory system.",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


@app.command()
def init(
    update: Annotated[bool, typer.Option("--update", help="Refresh templates, preserve project context.")] = False,
) -> None:
    """Initialize Byakugan in the current project."""
    from byakugan.commands.init import run
    run(update=update)


@app.command()
def update() -> None:
    """Refresh templates from master, preserve project-specific context."""
    from byakugan.commands.update import run
    run()


@app.command()
def sync() -> None:
    """Re-detect the project stack and update the stored profile if it has drifted."""
    from byakugan.commands.sync import run
    run()


@app.command()
def add(
    template: Annotated[str, typer.Argument(help="Template path, e.g. languages/python.md")],
) -> None:
    """Add a guideline template to this project."""
    from byakugan.commands.add import run
    run(template)


@app.command()
def remove(
    template: Annotated[str, typer.Argument(help="Template path to remove, e.g. languages/python.md")],
) -> None:
    """Remove a guideline template from this project."""
    from byakugan.commands.remove import run
    run(template)


@app.command()
def status() -> None:
    """Show the active Byakugan setup and system checks."""
    from byakugan.commands.status import run
    run()


@app.command(name="list")
def list_templates() -> None:
    """List all available bundled templates."""
    from byakugan.commands.list_cmd import run
    run()


@app.command()
def doctor() -> None:
    """Diagnose and repair the Byakugan setup (includes stack drift check)."""
    from byakugan.commands.doctor import run
    run()


@app.command()
def remember(
    note: Annotated[str, typer.Argument(help='Memory to store, e.g. "correction: do not use X"')],
    importance: Annotated[int, typer.Option("--importance", "-i", help="Importance 1-5 (auto-inferred if omitted).")] = 3,
) -> None:
    """Store a memory in this project's knowledge base."""
    from byakugan.commands.remember import run
    run(note, importance=importance)


# ── memories subcommand group ─────────────────────────────────────────────────

from byakugan.commands.memories import app as _memories_app

app.add_typer(
    _memories_app,
    name="memories",
    help="Browse, search, and manage the project memory database.",
)


@app.command()
def hook() -> None:
    """[Internal] PreToolUse hook runner — reads from stdin, writes to stdout."""
    from byakugan.hook_runner import run
    run()


def main() -> None:
    app()
