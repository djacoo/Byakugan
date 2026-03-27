"""byakugan add — add a template to the active set."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from byakugan.core import adapter, claude_md
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

    # Normalize template path
    template = template.strip().strip("/")

    if template in config.active_templates:
        console.print(f"[yellow]Template [bold]{template}[/bold] is already active.[/yellow]")
        raise typer.Exit()

    # Validate template exists in bundled set
    all_templates = adapter.list_bundled_templates()
    flat = {
        f"{cat}/{name}"
        for cat, names in all_templates.items()
        for name in names
    }
    if template not in flat:
        console.print(f"[red]Template [bold]{template}[/bold] not found.[/red]")
        console.print()
        console.print("Available templates:")
        for t in sorted(flat):
            console.print(f"  · {t}")
        raise typer.Exit(1)

    # Adapt and write
    with console.status(f"Adding {template}…"):
        dest = byakugan_dir / template
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = adapter.adapt_template(template, config.project)
        dest.write_text(content, encoding="utf-8")

        config.active_templates.append(template)
        config.last_updated = now_iso()
        save_config(config, byakugan_root)
        claude_md.write(config, byakugan_root)

    console.print(f"[bold green]✓[/bold green] Added [bold]{template}[/bold].")
