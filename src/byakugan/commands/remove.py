"""byakugan remove — remove a template from the active set."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from byakugan.core import claude_md
from byakugan.core.config import (
    find_byakugan_root,
    get_byakugan_dir,
    load_config,
    now_iso,
    save_config,
)

console = Console()


def run(template: str) -> None:
    root = Path.cwd()
    byakugan_root = find_byakugan_root(root)
    if byakugan_root is None:
        console.print("[red]No Byakugan setup found. Run [bold]byakugan init[/bold] first.[/red]")
        raise typer.Exit(1)

    byakugan_dir = get_byakugan_dir(byakugan_root)
    config = load_config(byakugan_root)

    template = template.strip().strip("/")

    if template not in config.active_templates:
        console.print(f"[yellow]Template [bold]{template}[/bold] is not active.[/yellow]")
        raise typer.Exit()

    confirmed = Confirm.ask(f"Remove [bold]{template}[/bold] from this project?", default=False)
    if not confirmed:
        console.print("Aborted.")
        raise typer.Exit()

    with console.status(f"Removing {template}…"):
        config.active_templates.remove(template)
        config.last_updated = now_iso()

        # Remove adapted file from .byakugan/
        dest = byakugan_dir / template
        if dest.exists():
            dest.unlink()

        save_config(config, byakugan_root)
        claude_md.write(config, byakugan_root)

    console.print(f"[bold green]✓[/bold green] Removed [bold]{template}[/bold].")
