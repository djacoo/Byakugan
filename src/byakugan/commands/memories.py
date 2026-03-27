"""byakugan memories — browse, search, and manage the project's memory database."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from byakugan.core.config import find_byakugan_root, get_memory_path
from byakugan.core import memory as mem

console = Console()

app = typer.Typer(
    name="memories",
    help="Browse, search, and manage the project memory database.",
    no_args_is_help=True,
)

TYPE_COLORS = {
    "correction": "red",
    "decision":   "blue",
    "preference": "cyan",
    "pattern":    "magenta",
    "note":       "white",
}

IMPORTANCE_STARS = {1: "·", 2: "◦", 3: "●", 4: "●●", 5: "●●●"}


def _require_root() -> tuple[Path, Path]:
    root = find_byakugan_root(Path.cwd())
    if root is None:
        console.print("[red]No Byakugan setup found. Run [bold]byakugan init[/bold] first.[/red]")
        raise typer.Exit(1)
    return root, get_memory_path(root)


@app.command(name="list")
def list_memories(
    limit: int = typer.Option(30, "--limit", "-n", help="Max memories to show."),
) -> None:
    """List all stored memories, sorted by importance."""
    _, db_path = _require_root()

    memories = mem.get_all(db_path, limit=limit)
    total = mem.count(db_path)

    if not memories:
        console.print("[dim]No memories stored yet.[/dim]")
        console.print()
        console.print('Store one: [bold]byakugan remember "correction: ..."[/bold]')
        return

    console.print()
    console.print(f"[bold cyan]◈ Memories[/bold cyan] — {total} total")
    console.print()

    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column("ID",  style="dim", width=5)
    table.add_column("Imp", width=4)
    table.add_column("Type", width=12)
    table.add_column("Content")
    table.add_column("Tags", style="dim", width=24)

    for m in memories:
        color = TYPE_COLORS.get(m.type, "white")
        stars = IMPORTANCE_STARS.get(m.importance, "?")
        short = m.content[:80] + ("…" if len(m.content) > 80 else "")
        tags_str = ", ".join(m.tags[:4]) if m.tags else ""
        surfaced = f"[dim](×{m.surface_count})[/dim]" if m.surface_count > 0 else ""
        table.add_row(
            str(m.id),
            stars,
            f"[{color}]{m.type}[/{color}]",
            f"{short} {surfaced}",
            tags_str,
        )

    console.print(table)
    if total > limit:
        console.print(f"[dim]Showing {limit} of {total}. Use --limit to see more.[/dim]")
    console.print()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search terms (space-separated, all must match)."),
    limit: int = typer.Option(20, "--limit", "-n"),
) -> None:
    """Search memories by content or tags."""
    _, db_path = _require_root()

    results = mem.search(db_path, query, limit=limit)

    if not results:
        console.print(f"[yellow]No memories matching '[bold]{query}[/bold]'.[/yellow]")
        return

    console.print()
    console.print(f"[bold cyan]◈ Search:[/bold cyan] {query} — {len(results)} result(s)")
    console.print()

    for m in results:
        color = TYPE_COLORS.get(m.type, "white")
        stars = IMPORTANCE_STARS.get(m.importance, "?")
        tags_str = f"  [dim]{', '.join(m.tags[:4])}[/dim]" if m.tags else ""
        console.print(f"  [dim]{m.id}[/dim]  {stars}  [{color}]{m.type}[/{color}]  {m.content}{tags_str}")

    console.print()


@app.command()
def forget(
    memory_id: int = typer.Argument(..., help="ID of the memory to delete (see 'list')."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Delete a memory by ID."""
    _, db_path = _require_root()

    # Show the memory before deleting
    all_mems = mem.get_all(db_path, limit=500)
    target = next((m for m in all_mems if m.id == memory_id), None)

    if target is None:
        console.print(f"[red]No memory with ID {memory_id}.[/red]")
        raise typer.Exit(1)

    color = TYPE_COLORS.get(target.type, "white")
    console.print()
    console.print(f"  [{color}]{target.type}[/{color}]  {target.content}")
    console.print()

    if not yes:
        confirmed = Confirm.ask("Delete this memory?", default=False)
        if not confirmed:
            console.print("Aborted.")
            raise typer.Exit()

    if mem.delete(db_path, memory_id):
        console.print(f"[bold green]✓[/bold green] Memory {memory_id} deleted.")
    else:
        console.print(f"[red]Could not delete memory {memory_id}.[/red]")
        raise typer.Exit(1)


@app.command()
def prune(
    days: int = typer.Option(90, "--days", "-d", help="Age threshold in days."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """
    Decay importance of stale memories and remove low-value ones.

    Two-step process:
    1. Decay importance by 1 for memories not surfaced in --days.
    2. Delete importance-1 memories older than --days.
    """
    _, db_path = _require_root()

    total_before = mem.count(db_path)
    console.print()
    console.print(f"[bold cyan]◈ Prune[/bold cyan] — {total_before} memories, threshold: {days} days")
    console.print()
    console.print("  Step 1: Decay stale memories (importance > 1 → importance - 1)")
    console.print(f"  Step 2: Delete importance-1 memories older than {days} days")
    console.print()

    if not yes:
        confirmed = Confirm.ask("Proceed?", default=True)
        if not confirmed:
            console.print("Aborted.")
            raise typer.Exit()

    decayed = mem.apply_decay(db_path, days_threshold=days)
    removed = mem.prune(db_path, days_threshold=days)
    total_after = mem.count(db_path)

    console.print(f"[green]✓[/green] Decayed {decayed} memor{'y' if decayed == 1 else 'ies'}.")
    console.print(f"[green]✓[/green] Removed {removed} low-value memor{'y' if removed == 1 else 'ies'}.")
    console.print(f"[dim]{total_before} → {total_after} memories.[/dim]")
    console.print()
