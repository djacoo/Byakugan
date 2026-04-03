"""byakugan doctor — diagnose and repair the Byakugan setup."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from byakugan.core import adapter, claude_md, hooks
from byakugan.core.config import (
    find_byakugan_root,
    get_byakugan_dir,
    get_db_path,
    load_config,
)
from byakugan.core.detector import detect_drift
from byakugan.core.database import init_db, get_tables, get_pending_event_count
from byakugan.core.superpowers import is_superpowers_installed

console = Console()

OK   = "[bold green]✓[/bold green]"
FAIL = "[bold red]✗[/bold red]"
WARN = "[bold yellow]![/bold yellow]"


def run() -> None:
    root = Path.cwd()
    byakugan_root = find_byakugan_root(root)

    console.print()
    console.print("[bold cyan]◈ Byakugan[/bold cyan] — doctor")
    console.print()

    issues: list[str] = []

    # ── Check 1: initialized ─────────────────────────────────────────────────
    if byakugan_root is None:
        console.print(f"{FAIL} Not initialized in this project.")
        console.print("     Run [bold]byakugan init[/bold] to set up.")
        console.print()
        raise typer.Exit(1)
    console.print(f"{OK} Initialized at [dim]{byakugan_root}[/dim]")

    byakugan_dir = get_byakugan_dir(byakugan_root)
    config = load_config(byakugan_root)

    # ── Check 2: byakugan in PATH ────────────────────────────────────────────
    if hooks.byakugan_in_path():
        console.print(f"{OK} [bold]byakugan[/bold] found in PATH")
    else:
        console.print(f"{WARN} [bold]byakugan[/bold] not found in PATH")
        console.print("     Install with: [dim]uv tool install byakugan[/dim]")
        issues.append("byakugan_not_in_path")

    # ── Check: superpowers ───────────────────────────────────────────────
    if is_superpowers_installed():
        console.print(f"{OK} Superpowers detected")
    else:
        console.print(f"{WARN} Superpowers not detected")
        console.print("     Install superpowers for full workflow support")
        issues.append("superpowers_missing")

    # ── Check 3: hooks installed ─────────────────────────────────────────────
    if hooks.hooks_installed(byakugan_root):
        console.print(f"{OK} Hooks installed in [dim].claude/settings.local.json[/dim]")
    else:
        console.print(f"{FAIL} Hooks not installed")
        issues.append("hooks_missing")

    # ── Check 4: CLAUDE.md ───────────────────────────────────────────────────
    claude_path = byakugan_root / "CLAUDE.md"
    if claude_path.exists() and claude_md.is_managed(byakugan_root):
        console.print(f"{OK} CLAUDE.md present and managed")
    elif claude_path.exists():
        console.print(f"{WARN} CLAUDE.md exists but is not managed by Byakugan")
        issues.append("claude_md_unmanaged")
    else:
        console.print(f"{FAIL} CLAUDE.md missing")
        issues.append("claude_md_missing")

    # ── Check 5: template files ──────────────────────────────────────────────
    missing_templates: list[str] = []
    for t in config.active_templates:
        dest = byakugan_dir / t
        if not dest.exists():
            missing_templates.append(t)

    if missing_templates:
        console.print(f"{FAIL} {len(missing_templates)} template file(s) missing:")
        for t in missing_templates:
            console.print(f"     · {t}")
        issues.append("templates_missing")
    else:
        console.print(f"{OK} All {len(config.active_templates)} template file(s) present")

    # ── Check 6: database ────────────────────────────────────────────────
    db_path = get_db_path(byakugan_root)
    if db_path.exists():
        tables = get_tables(db_path)
        if len(tables) == 4:
            from byakugan.core.memory import count
            n = count(db_path)
            console.print(f"{OK} Database present — {n} memor{'y' if n == 1 else 'ies'}, {len(tables)} tables")
        else:
            console.print(f"{FAIL} Database schema incomplete — {len(tables)}/4 tables")
            issues.append("db_schema_incomplete")

        # Compression backlog check
        pending = get_pending_event_count(db_path)
        if pending > 200:
            console.print(f"{WARN} Compression backlog: {pending} pending events")
            console.print("     Run [bold]byakugan session save[/bold] to compress")
            issues.append("compression_backlog")
        elif pending > 0:
            console.print(f"{OK} {pending} pending event(s)")

        # Legacy backup check
        bak_path = byakugan_dir / "memory.db.bak"
        if bak_path.exists():
            import os, time as _time
            age_days = (_time.time() - os.path.getmtime(str(bak_path))) / 86400
            if age_days > 30:
                console.print(f"{WARN} Legacy memory.db.bak is {int(age_days)} days old — safe to delete")
    else:
        console.print(f"{FAIL} Database missing")
        issues.append("memory_missing")

    # ── Check 7: stack drift ─────────────────────────────────────────────────
    console.print()
    console.print("[dim]Checking for stack drift…[/dim]")
    try:
        drift, _ = detect_drift(byakugan_root, config.project)
        if drift["added"] or drift["removed"]:
            console.print(f"{WARN} Stack drift detected:")
            for item in drift["added"]:
                console.print(f"     [cyan]+[/cyan] {item}")
            for item in drift["removed"]:
                console.print(f"     [red]-[/red] {item}")
            console.print("     Run [bold]byakugan sync[/bold] to update profile.")
            issues.append("stack_drift")
        else:
            console.print(f"{OK} No stack drift — profile matches current project")
    except Exception:
        console.print(f"{WARN} Could not check for stack drift")

    console.print()

    # ── Auto-repair ──────────────────────────────────────────────────────────
    repairable = [i for i in issues if i not in {"stack_drift", "byakugan_not_in_path", "superpowers_missing", "compression_backlog"}]

    if not repairable and "stack_drift" not in issues:
        console.print("[bold green]Everything looks good.[/bold green]")
        console.print()
        return

    if repairable:
        console.print(f"[yellow]{len(repairable)} repairable issue(s) found.[/yellow]")
        fix = Confirm.ask("Attempt auto-repair?", default=True)
        if fix:
            console.print()
            with console.status("Repairing…"):
                if "hooks_missing" in repairable:
                    hooks.install_hooks(byakugan_root)
                    console.print(f"{OK} Hooks reinstalled.")

                if "claude_md_missing" in repairable or "claude_md_unmanaged" in repairable:
                    claude_md.write(config, byakugan_root)
                    console.print(f"{OK} CLAUDE.md regenerated.")

                if "templates_missing" in repairable:
                    for t in missing_templates:
                        dest = byakugan_dir / t
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        content = adapter.adapt_template(t, config.project)
                        dest.write_text(content, encoding="utf-8")
                    console.print(f"{OK} Missing templates restored ({len(missing_templates)}).")

                if "memory_missing" in repairable:
                    init_db(db_path)
                    console.print(f"{OK} Database initialized.")

                if "db_schema_incomplete" in repairable:
                    init_db(db_path)
                    console.print(f"{OK} Database schema repaired.")

            console.print()
            console.print("[bold green]Repair complete.[/bold green]")

    if "stack_drift" in issues:
        console.print()
        console.print("[dim]Run [bold]byakugan sync[/bold] to reconcile stack changes.[/dim]")

    console.print()
