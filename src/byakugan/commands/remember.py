"""byakugan remember — store a memory in the project's knowledge base."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from byakugan.core.config import find_byakugan_root, get_memory_path
from byakugan.core.memory import VALID_TYPES, TYPE_PREFIXES, store

console = Console()


def run(note: str) -> None:
    root = Path.cwd()
    byakugan_root = find_byakugan_root(root)
    if byakugan_root is None:
        console.print("[red]No Byakugan setup found. Run [bold]byakugan init[/bold] first.[/red]")
        raise typer.Exit(1)

    db_path = get_memory_path(byakugan_root)
    note = note.strip()

    if not note:
        console.print("[red]Note cannot be empty.[/red]")
        raise typer.Exit(1)

    # Infer type from prefix (e.g. "correction: ...", "preference: ...")
    memory_type = "note"
    content = note
    for prefix, t in TYPE_PREFIXES.items():
        if note.lower().startswith(prefix + ":"):
            memory_type = t
            content = note[len(prefix) + 1:].strip()
            break

    store(db_path, memory_type=memory_type, content=content)

    console.print(f"[bold green]✓[/bold green] Stored [{memory_type}]: {content[:80]}{'…' if len(content) > 80 else ''}")
