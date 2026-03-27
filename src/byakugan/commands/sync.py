"""byakugan sync — re-detect the project stack and report drift from the stored profile."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from byakugan.core import adapter, claude_md
from byakugan.core.config import (
    find_byakugan_root,
    get_byakugan_dir,
    get_memory_path,
    load_config,
    now_iso,
    save_config,
)
from byakugan.core.detector import detect, detect_drift
from byakugan.core.memory import init_db

console = Console()

OK   = "[bold green]✓[/bold green]"
WARN = "[bold yellow]![/bold yellow]"
NEW  = "[bold cyan]+[/bold cyan]"
DROP = "[bold red]-[/bold red]"


def run() -> None:
    root = Path.cwd()
    byakugan_root = find_byakugan_root(root)

    if byakugan_root is None:
        console.print("[red]No Byakugan setup found. Run [bold]byakugan init[/bold] first.[/red]")
        raise typer.Exit(1)

    config = load_config(byakugan_root)
    stored_profile = config.project
    byakugan_dir = get_byakugan_dir(byakugan_root)

    console.print()
    console.print(f"[bold cyan]◈ Byakugan sync[/bold cyan] — re-detecting [bold]{stored_profile.name or byakugan_root.name}[/bold]")
    console.print()

    with console.status("Scanning project…"):
        drift = detect_drift(byakugan_root, stored_profile)
        fresh = detect(byakugan_root)

    added   = drift["added"]
    removed = drift["removed"]

    if not added and not removed:
        console.print(f"{OK} No stack drift detected. Profile is up to date.")
        console.print()
        return

    # Show diff
    if added:
        console.print("New detections:")
        for item in added:
            console.print(f"  {NEW} {item}")
    if removed:
        console.print("No longer detected:")
        for item in removed:
            console.print(f"  {DROP} {item}")

    console.print()

    # Identify new templates to suggest
    existing_templates = set(config.active_templates)
    new_templates = [
        t for t in fresh.suggested_templates
        if t not in existing_templates
    ]
    removed_templates: list[str] = []  # we don't auto-remove; user decides

    if new_templates:
        console.print("Templates available for new detections:")
        for t in new_templates:
            console.print(f"  {NEW} {t}")
        console.print()

    update = Confirm.ask("Update stored profile with current detections?", default=True)
    if not update:
        console.print("Profile unchanged.")
        console.print()
        return

    # Update the stored profile with fresh data
    fp = fresh.profile

    # Merge: prefer fresh detections but keep user-provided fields
    if fp.languages:
        stored_profile.languages = fp.languages
    if fp.frameworks:
        stored_profile.frameworks = fp.frameworks
    if fp.package_manager:
        stored_profile.package_manager = fp.package_manager
    if fp.test_runner:
        stored_profile.test_runner = fp.test_runner
    if fp.linter:
        stored_profile.linter = fp.linter
    if fp.formatter:
        stored_profile.formatter = fp.formatter
    if fp.type_checker:
        stored_profile.type_checker = fp.type_checker
    if fp.python_version:
        stored_profile.python_version = fp.python_version
    if fp.node_version:
        stored_profile.node_version = fp.node_version
    if fp.database and not stored_profile.database:
        stored_profile.database = fp.database

    config.project = stored_profile

    # Optionally add newly suggested templates
    if new_templates:
        add_them = Confirm.ask(f"Add {len(new_templates)} new template(s)?", default=True)
        if add_them:
            with console.status("Adapting new templates…"):
                for t in new_templates:
                    dest = byakugan_dir / t
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    content = adapter.adapt_template(t, stored_profile)
                    dest.write_text(content, encoding="utf-8")
                config.active_templates.extend(new_templates)

    # Refresh existing template context blocks with new profile
    refresh = Confirm.ask("Refresh context blocks in existing templates?", default=True)
    if refresh:
        with console.status("Refreshing templates…"):
            for t in config.active_templates:
                dest = byakugan_dir / t
                if dest.exists():
                    existing = dest.read_text(encoding="utf-8")
                    new_content = adapter.update_adapted_template(existing, t, stored_profile)
                    dest.write_text(new_content, encoding="utf-8")

    config.last_updated = now_iso()
    save_config(config, byakugan_root)
    claude_md.write(config, byakugan_root)

    console.print(f"{OK} Profile updated.")
    if new_templates and add_them:
        console.print(f"{OK} Added {len(new_templates)} template(s).")
    console.print()
    console.print("Run [bold]byakugan status[/bold] to verify.")
    console.print()
