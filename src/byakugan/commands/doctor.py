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
    get_memory_path,
    load_config,
)
from byakugan.core.memory import init_db

console = Console()

OK = "[bold green]✓[/bold green]"
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

    # ── Check 6: memory DB ───────────────────────────────────────────────────
    mem_path = get_memory_path(byakugan_root)
    if mem_path.exists():
        console.print(f"{OK} Memory DB present at [dim]{mem_path.name}[/dim]")
    else:
        console.print(f"{FAIL} Memory DB missing")
        issues.append("memory_missing")

    console.print()

    # ── Auto-repair ──────────────────────────────────────────────────────────
    if not issues:
        console.print("[bold green]Everything looks good.[/bold green]")
        console.print()
        return

    console.print(f"[yellow]{len(issues)} issue(s) found.[/yellow]")
    fix = Confirm.ask("Attempt auto-repair?", default=True)
    if not fix:
        raise typer.Exit(1)

    console.print()
    with console.status("Repairing…"):
        if "hooks_missing" in issues:
            hooks.install_hooks(byakugan_root)
            console.print(f"{OK} Hooks reinstalled.")

        if "claude_md_missing" in issues or "claude_md_unmanaged" in issues:
            claude_md.write(config, byakugan_root)
            console.print(f"{OK} CLAUDE.md regenerated.")

        if "templates_missing" in issues:
            for t in missing_templates:
                dest = byakugan_dir / t
                dest.parent.mkdir(parents=True, exist_ok=True)
                content = adapter.adapt_template(t, config.project)
                dest.write_text(content, encoding="utf-8")
            console.print(f"{OK} Missing templates restored ({len(missing_templates)}).")

        if "memory_missing" in issues:
            init_db(mem_path)
            console.print(f"{OK} Memory DB initialized.")

    console.print()
    console.print("[bold green]Repair complete.[/bold green]")
    console.print()
