"""byakugan deinit — remove Byakugan from the current project."""
from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from byakugan.core import hooks
from byakugan.core.config import find_byakugan_root, get_byakugan_dir, load_config

console = Console()

OK   = "[bold green]✓[/bold green]"
SKIP = "[dim]·[/dim]"


def run(yes: bool = False) -> None:
    root = Path.cwd()
    byakugan_root = find_byakugan_root(root)

    console.print()
    console.print("[bold cyan]◈ Byakugan[/bold cyan] — deinit")
    console.print()

    if byakugan_root is None:
        console.print("[yellow]No Byakugan setup found in this project.[/yellow]")
        console.print()
        raise typer.Exit()

    console.print(f"  Project root: [dim]{byakugan_root}[/dim]")
    console.print()
    console.print("This will:")
    console.print("  · Remove Byakugan hooks from [dim].claude/settings.local.json[/dim]")
    console.print("  · Optionally delete [dim].byakugan/[/dim] (guidelines + memory database)")
    console.print("  · Optionally delete [dim]CLAUDE.md[/dim]")
    console.print()

    if not yes:
        confirmed = Confirm.ask("Proceed?", default=False)
        if not confirmed:
            console.print("Aborted.")
            console.print()
            raise typer.Exit()

    # Uninstall hooks if present
    if hooks.hooks_installed(byakugan_root):
        hooks.uninstall_hooks(byakugan_root)
        console.print(f"{OK} Hook removed from [dim].claude/settings.local.json[/dim]")
    else:
        console.print(f"{SKIP} No hook found in [dim].claude/settings.local.json[/dim]")

    # Offer to uninstall superpowers if Byakugan installed it
    try:
        config = load_config(byakugan_root)
        if config.superpowers_installed_by_byakugan:
            if yes or Confirm.ask("Uninstall superpowers? (Byakugan installed it)"):
                import subprocess
                try:
                    subprocess.run(["claude", "plugin", "uninstall", "superpowers"],
                                   capture_output=True, timeout=30)
                    console.print(f"{OK} Superpowers uninstalled")
                except Exception:
                    console.print("[yellow]Could not uninstall superpowers automatically[/yellow]")
    except Exception:
        pass

    # Optionally remove .byakugan/
    byakugan_dir = get_byakugan_dir(byakugan_root)
    if byakugan_dir.exists():
        if yes or Confirm.ask("Delete .byakugan/ (guidelines + memory database)?", default=False):
            shutil.rmtree(byakugan_dir)
            console.print(f"{OK} Deleted [dim].byakugan/[/dim]")
        else:
            console.print(f"{SKIP} Kept [dim].byakugan/[/dim]")

    # Optionally remove CLAUDE.md
    claude_md_path = byakugan_root / "CLAUDE.md"
    if claude_md_path.exists():
        if yes or Confirm.ask("Delete CLAUDE.md?", default=False):
            claude_md_path.unlink()
            console.print(f"{OK} Deleted [dim]CLAUDE.md[/dim]")
        else:
            console.print(f"{SKIP} Kept [dim]CLAUDE.md[/dim]")

    console.print()
    console.print("[bold green]Byakugan removed.[/bold green]")
    console.print("Run [bold]byakugan init[/bold] to set it up again.")
    console.print()
