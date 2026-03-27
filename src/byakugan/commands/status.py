"""byakugan status — show the active Byakugan setup."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from byakugan.core import hooks
from byakugan.core.adapter import template_display_name
from byakugan.core.config import (
    find_byakugan_root,
    get_byakugan_dir,
    get_memory_path,
    load_config,
)
from byakugan.core.memory import count

console = Console()


def run() -> None:
    root = Path.cwd()
    byakugan_root = find_byakugan_root(root)
    if byakugan_root is None:
        console.print("[red]No Byakugan setup found. Run [bold]byakugan init[/bold] first.[/red]")
        raise typer.Exit(1)

    config = load_config(byakugan_root)
    byakugan_dir = get_byakugan_dir(byakugan_root)
    profile = config.project

    console.print()
    console.print("[bold cyan]◈ Byakugan[/bold cyan] — [bold]{}[/bold]".format(
        profile.name or byakugan_root.name
    ))
    console.print()

    # ── Project info ─────────────────────────────────────────────────────────
    info = Table(show_header=False, box=None, padding=(0, 2))
    info.add_column(style="dim", width=18)
    info.add_column()

    if profile.languages:
        info.add_row("Languages", ", ".join(profile.languages))
    if profile.frameworks:
        info.add_row("Frameworks", ", ".join(profile.frameworks))
    if profile.package_manager:
        info.add_row("Package manager", profile.package_manager)
    if profile.test_runner:
        info.add_row("Test runner", profile.test_runner)
    if profile.linter:
        info.add_row("Linter", profile.linter)
    if profile.formatter:
        info.add_row("Formatter", profile.formatter)
    if profile.database:
        info.add_row("Database", profile.database)
    if profile.deployment:
        info.add_row("Deployment", profile.deployment)

    info.add_row("Initialized", config.initialized_at[:10])
    if config.last_updated:
        info.add_row("Last updated", config.last_updated[:10])

    console.print("Project:", style="bold")
    console.print(info)
    console.print()

    # ── Active templates ─────────────────────────────────────────────────────
    console.print("Active guidelines:", style="bold")
    tmpl_table = Table(show_header=True, box=None, padding=(0, 2))
    tmpl_table.add_column("Template", style="cyan")
    tmpl_table.add_column("Purpose", style="dim")
    tmpl_table.add_column("File", style="dim")

    for t in config.active_templates:
        dest = byakugan_dir / t
        file_status = "[green]✓[/green]" if dest.exists() else "[red]missing[/red]"
        tmpl_table.add_row(t, template_display_name(t), file_status)

    console.print(tmpl_table)
    console.print()

    # ── System checks ─────────────────────────────────────────────────────────
    hooks_ok = hooks.hooks_installed(byakugan_root)
    byakugan_ok = hooks.byakugan_in_path()
    mem_path = get_memory_path(byakugan_root)
    mem_count = count(mem_path) if mem_path.exists() else 0
    claude_md_path = byakugan_root / "CLAUDE.md"

    checks = Table(show_header=False, box=None, padding=(0, 2))
    checks.add_column(style="dim", width=18)
    checks.add_column()

    checks.add_row("Hooks", "[green]installed[/green]" if hooks_ok else "[red]not installed[/red]")
    checks.add_row("byakugan in PATH", "[green]yes[/green]" if byakugan_ok else "[yellow]not found[/yellow]")
    checks.add_row("CLAUDE.md", "[green]present[/green]" if claude_md_path.exists() else "[red]missing[/red]")
    checks.add_row("Memory entries", str(mem_count))

    console.print("System:", style="bold")
    console.print(checks)
    console.print()

    if not hooks_ok or not byakugan_ok:
        console.print("[yellow]Run [bold]byakugan doctor[/bold] for diagnostics.[/yellow]")
        console.print()
