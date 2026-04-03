"""byakugan session — manage session summaries."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from byakugan.core.config import find_byakugan_root, get_db_path
from byakugan.core.database import get_summaries

console = Console()
app = typer.Typer(help="Session summary management")


def _require_root() -> tuple:
    root = find_byakugan_root()
    if root is None:
        console.print("[red]Not initialized. Run `byakugan init` first.[/red]")
        raise SystemExit(1)
    return root, get_db_path(root)


@app.command("list")
def list_sessions(
    period: str = typer.Option(None, help="Filter by period: hourly, daily, weekly"),
    limit: int = typer.Option(20, "-n", help="Max results"),
) -> None:
    """List session summaries."""
    _, db_path = _require_root()
    summaries = get_summaries(db_path, period=period, limit=limit)

    if not summaries:
        console.print("[dim]No session summaries yet.[/dim]")
        return

    table = Table(title="Session Summaries")
    table.add_column("ID", style="cyan")
    table.add_column("Period", style="green")
    table.add_column("Date", style="yellow")
    table.add_column("Preview")
    table.add_column("Events", justify="right")

    for s in summaries:
        preview = s["content"][:80] + ("…" if len(s["content"]) > 80 else "")
        table.add_row(
            str(s["id"]),
            s["period"],
            s["created_at"][:16],
            preview,
            str(s["source_event_count"]),
        )

    console.print(table)


@app.command("show")
def show_session(
    summary_id: int = typer.Argument(help="Summary ID to display"),
) -> None:
    """Show full content of a session summary."""
    _, db_path = _require_root()
    summaries = get_summaries(db_path)
    match = [s for s in summaries if s["id"] == summary_id]

    if not match:
        console.print(f"[red]Summary #{summary_id} not found.[/red]")
        raise SystemExit(1)

    s = match[0]
    console.print(f"[cyan]Summary #{s['id']}[/cyan] ({s['period']}) — {s['created_at'][:16]}")
    console.print(f"Events compressed: {s['source_event_count']}")
    console.print()
    console.print(s["content"])


@app.command("save")
def save_session() -> None:
    """Manually trigger compression now."""
    _, db_path = _require_root()

    from byakugan.core.compression import compress_events
    from byakugan.core.database import get_pending_event_count

    count = get_pending_event_count(db_path)
    if count == 0:
        console.print("[dim]No pending events to compress.[/dim]")
        return

    console.print(f"Compressing {count} events...")
    try:
        if compress_events(db_path):
            console.print("[green]✓[/green] Compression complete.")
        else:
            console.print("[yellow]Not enough events for compression threshold.[/yellow]")
    except Exception as e:
        console.print(f"[red]Compression failed: {e}[/red]")
