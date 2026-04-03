"""Byakugan CLI — active guidelines and memory system for Claude Code."""
from __future__ import annotations

from typing import Annotated, Optional

import typer

from byakugan import __version__

app = typer.Typer(
    name="byakugan",
    help="Active guidelines and memory system for Claude Code.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"byakugan {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-V", callback=_version_callback, is_eager=True,
                     help="Show version and exit"),
    ] = None,
) -> None:
    pass


@app.command()
def init(update: bool = typer.Option(False, "--update", help="Update existing setup")) -> None:
    """Initialize Byakugan in the current project."""
    from byakugan.commands.init import run
    run(update=update)


@app.command()
def update() -> None:
    """Refresh templates and guidelines."""
    from byakugan.commands.update import run
    run()


@app.command()
def sync() -> None:
    """Re-detect stack and sync templates."""
    from byakugan.commands.sync import run
    run()


@app.command()
def add(template: Annotated[str, typer.Argument(help="Template to add")]) -> None:
    """Add a template to active guidelines."""
    from byakugan.commands.add import run
    run(template)


@app.command()
def remove(template: Annotated[str, typer.Argument(help="Template to remove")]) -> None:
    """Remove a template from active guidelines."""
    from byakugan.commands.remove import run
    run(template)


@app.command()
def status() -> None:
    """Show current Byakugan setup."""
    from byakugan.commands.status import run
    run()


@app.command("list")
def list_templates() -> None:
    """List all available templates."""
    from byakugan.commands.list_cmd import run
    run()


@app.command()
def doctor() -> None:
    """Diagnose and auto-repair Byakugan setup."""
    from byakugan.commands.doctor import run
    run()


@app.command()
def remember(
    note: Annotated[str, typer.Argument(help="Memory to store")],
    importance: int = typer.Option(3, "-i", help="Importance (1-5)"),
    file: Optional[str] = typer.Option(None, "-f", help="Related file"),
) -> None:
    """Store a memory for future sessions."""
    from byakugan.commands.remember import run
    run(note, importance, file)


@app.command()
def handoff(
    note: Annotated[str, typer.Argument(help="Handoff note for next session")],
) -> None:
    """Save a handoff note for the next session."""
    from byakugan.commands.handoff import run
    run(note)


@app.command()
def deinit(yes: bool = typer.Option(False, "-y", help="Skip confirmations")) -> None:
    """Remove Byakugan from the current project."""
    from byakugan.commands.deinit import run
    run(yes)


# ── Subcommand groups ────────────────────────────────────────────────────────

from byakugan.commands.memories import app as memories_app
app.add_typer(memories_app, name="memories", help="Manage stored memories")

from byakugan.commands.session import app as session_app
app.add_typer(session_app, name="session", help="Manage session summaries")


# ── Hidden hook command ──────────────────────────────────────────────────────

@app.command(hidden=True)
def hook(
    hook_type: str = typer.Option("pre-tool", "--type", "-t", help="Hook type: session-start, pre-tool, post-tool"),
) -> None:
    """Internal: called by Claude Code hooks."""
    from byakugan.hook_runner import run as hook_run
    hook_run(hook_type=hook_type)
