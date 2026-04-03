"""byakugan handoff — save a session handoff note."""
from __future__ import annotations

import subprocess

from rich.console import Console

from byakugan.core.config import find_byakugan_root, get_db_path
from byakugan.core.database import save_handoff, get_active_handoff

console = Console()


def run(note: str) -> None:
    root = find_byakugan_root()
    if root is None:
        console.print("[red]Not initialized. Run `byakugan init` first.[/red]")
        raise SystemExit(1)

    db_path = get_db_path(root)

    # Auto-detect current branch
    branch = None
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5, cwd=str(root),
        )
        branch = result.stdout.strip() or None
    except Exception:
        pass

    save_handoff(db_path, note, branch=branch)
    console.print(f"[green]✓[/green] Handoff saved")
    if branch:
        console.print(f"  branch: {branch}")
    console.print(f"  note: {note}")
