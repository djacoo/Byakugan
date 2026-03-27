"""byakugan remember — store a memory in the project's knowledge base."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from byakugan.core.config import find_byakugan_root, get_memory_path
from byakugan.core.memory import (
    VALID_TYPES,
    TYPE_PREFIXES,
    infer_importance,
    is_duplicate,
    store,
)

console = Console()


def run(note: str, importance: int = 3) -> None:
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

    # Parse type prefix (e.g. "correction: ...", "preference: ...")
    memory_type = "note"
    content = note
    for prefix, t in TYPE_PREFIXES.items():
        if note.lower().startswith(prefix):
            memory_type = t
            content = note[len(prefix):].strip()
            break

    # Auto-infer importance from content keywords (unless user set it explicitly)
    final_importance = infer_importance(content, importance)

    # Deduplication check
    dup_id = is_duplicate(db_path, content)
    if dup_id is not None:
        console.print(f"[yellow]⚠ A similar memory already exists (ID {dup_id}).[/yellow]")
        console.print(f"  Run [bold]byakugan memories list[/bold] to review it.")
        confirmed = Confirm.ask("Store anyway?", default=False)
        if not confirmed:
            console.print("Not stored.")
            return

    store(db_path, content=content, memory_type=memory_type, importance=final_importance)

    imp_note = f" (importance: {final_importance}/5)" if final_importance != 3 else ""
    console.print(
        f"[bold green]✓[/bold green] Stored [{memory_type}]{imp_note}: "
        f"{content[:80]}{'…' if len(content) > 80 else ''}"
    )
