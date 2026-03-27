"""byakugan init — initialize Byakugan in the current project."""
from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich import print as rprint

from byakugan.core import adapter, hooks, claude_md
from byakugan.core.config import (
    ByakuganConfig,
    ProjectProfile,
    BYAKUGAN_DIR,
    find_byakugan_root,
    get_byakugan_dir,
    load_config,
    now_iso,
    save_config,
    get_memory_path,
)
from byakugan.core.detector import detect, LANGUAGE_TO_TEMPLATE
from byakugan.core.memory import init_db

console = Console()


def run(update: bool = False) -> None:
    root = Path.cwd()
    byakugan_dir = get_byakugan_dir(root)

    if update:
        _run_update(root, byakugan_dir)
        return

    if find_byakugan_root(root) is not None:
        console.print("[yellow]Byakugan is already initialized in this project.[/yellow]")
        console.print("Run [bold]byakugan update[/bold] to refresh, or [bold]byakugan status[/bold] to inspect.")
        raise typer.Exit()

    console.print()
    console.print("[bold cyan]◈ Byakugan[/bold cyan] — initializing in [bold]{}[/bold]".format(root.name))
    console.print()

    # ── Detection ──────────────────────────────────────────────────────────────
    with console.status("Scanning project…"):
        detection = detect(root)

    profile = detection.profile
    suggested = detection.suggested_templates

    _print_detected(profile, suggested, detection.confidence)
    console.print()

    # ── Template selection ─────────────────────────────────────────────────────
    active_templates = _select_templates(suggested)
    if not active_templates:
        console.print("[red]No guidelines selected. Aborting.[/red]")
        raise typer.Exit(1)

    console.print()

    # ── Clarifying questions ───────────────────────────────────────────────────
    profile = _ask_clarifying_questions(profile, active_templates)
    console.print()

    # ── Build config ───────────────────────────────────────────────────────────
    config = ByakuganConfig(
        initialized_at=now_iso(),
        active_templates=active_templates,
        project=profile,
    )

    # ── Write files ────────────────────────────────────────────────────────────
    with console.status("Setting up Byakugan…"):
        byakugan_dir.mkdir(parents=True, exist_ok=True)

        # Adapt and write each template
        for t in active_templates:
            dest = byakugan_dir / t
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = adapter.adapt_template(t, profile)
            dest.write_text(content, encoding="utf-8")

        # Save config
        save_config(config, root)

        # Generate CLAUDE.md
        claude_md.write(config, root)

        # Install hooks
        hooks.install_hooks(root)

        # Init memory DB
        init_db(get_memory_path(root))

        # Update .gitignore
        _update_gitignore(root)

    # ── Done ───────────────────────────────────────────────────────────────────
    console.print("[bold green]✓[/bold green] Byakugan initialized.")
    console.print()
    console.print("  [dim]Guidelines:[/dim]   .byakugan/")
    console.print("  [dim]Entry point:[/dim]  CLAUDE.md")
    console.print("  [dim]Memory:[/dim]       .byakugan/memory.db")
    console.print("  [dim]Hooks:[/dim]        .claude/settings.local.json")
    console.print()
    console.print("Run [bold]byakugan status[/bold] to inspect the active setup.")
    console.print()


def _run_update(root: Path, byakugan_dir: Path) -> None:
    """Re-run init in update mode: refresh templates, preserve project context."""
    if not byakugan_dir.exists():
        console.print("[red]No Byakugan setup found. Run [bold]byakugan init[/bold] first.[/red]")
        raise typer.Exit(1)

    config = load_config(root)
    profile = config.project

    console.print()
    console.print("[bold cyan]◈ Byakugan[/bold cyan] — updating [bold]{}[/bold]".format(root.name))
    console.print()

    updated = 0
    with console.status("Refreshing templates from master…"):
        for t in config.active_templates:
            dest = byakugan_dir / t
            if dest.exists():
                existing = dest.read_text(encoding="utf-8")
                new_content = adapter.update_adapted_template(existing, t, profile)
            else:
                new_content = adapter.adapt_template(t, profile)
                dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(new_content, encoding="utf-8")
            updated += 1

        config.last_updated = now_iso()
        save_config(config, root)
        claude_md.write(config, root)
        hooks.install_hooks(root)

    console.print(f"[bold green]✓[/bold green] Updated {updated} template(s).")
    console.print("Project-specific context was preserved.")
    console.print()


def _print_detected(profile: ProjectProfile, suggested: list[str], confidence: dict) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()

    if profile.languages:
        table.add_row("Languages", ", ".join(profile.languages))
    if profile.frameworks:
        table.add_row("Frameworks", ", ".join(profile.frameworks))
    if profile.package_manager:
        table.add_row("Package manager", profile.package_manager)
    if profile.test_runner:
        table.add_row("Test runner", profile.test_runner)
    if profile.linter:
        table.add_row("Linter", profile.linter)
    if profile.formatter:
        table.add_row("Formatter", profile.formatter)

    console.print("Detected:", style="bold")
    console.print(table)
    console.print()

    console.print("Suggested guidelines:", style="bold")
    for t in suggested:
        how = confidence.get(t, "detected")
        tag = "[dim](inferred)[/dim]" if how == "inferred" else "[green](detected)[/green]"
        console.print(f"  [cyan]·[/cyan] {t}  {tag}")


def _select_templates(suggested: list[str]) -> list[str]:
    """Let user confirm, remove, or add templates."""
    console.print("Template selection:", style="bold")
    console.print("  Press [bold]Enter[/bold] to accept all suggestions.")
    console.print()

    accept_all = Confirm.ask("  Accept all suggested guidelines?", default=True)

    if accept_all:
        active = list(suggested)
    else:
        active = []
        all_templates = adapter.list_bundled_templates()
        flat = [
            f"{cat}/{name}"
            for cat, names in all_templates.items()
            for name in names
        ]
        console.print()
        console.print("Available templates (enter comma-separated list, e.g. languages/python.md,project-types/web-backend.md):")
        for t in flat:
            marker = "[cyan]✓[/cyan]" if t in suggested else " "
            console.print(f"  {marker} {t}")
        console.print()
        raw = Prompt.ask("Select templates").strip()
        if raw:
            active = [t.strip() for t in raw.split(",") if t.strip()]

    # Offer to add more
    console.print()
    add_more = Confirm.ask("Add any additional templates?", default=False)
    if add_more:
        all_templates = adapter.list_bundled_templates()
        flat = [
            f"{cat}/{name}"
            for cat, names in all_templates.items()
            for name in names
            if f"{cat}/{name}" not in active
        ]
        console.print()
        for t in flat:
            console.print(f"  · {t}")
        console.print()
        raw = Prompt.ask("Add (comma-separated, Enter to skip)", default="")
        if raw.strip():
            for t in raw.split(","):
                t = t.strip()
                if t and t not in active:
                    active.append(t)

    return active


def _ask_clarifying_questions(profile: ProjectProfile, active_templates: list[str]) -> ProjectProfile:
    """Ask the user for project-specific details that cannot be auto-detected."""
    console.print("Project details:", style="bold")
    console.print("  [dim]These refine how guidelines are adapted to your project.[/dim]")
    console.print()

    profile.name = Prompt.ask("  Project name", default=profile.name or "")

    # Database — only if backend/data templates are active
    backend_templates = {"project-types/web-backend.md", "project-types/fullstack-web.md",
                         "project-types/api-service.md", "project-types/data-engineering.md"}
    if any(t in backend_templates for t in active_templates) and not profile.database:
        db = Prompt.ask(
            "  Primary database",
            choices=["postgresql", "mysql", "sqlite", "mongodb", "redis", "none", "other"],
            default="none",
        )
        profile.database = db if db != "none" else None

    # Deployment — for backend/infra projects
    infra_templates = {"project-types/web-backend.md", "project-types/fullstack-web.md",
                       "project-types/devops-infrastructure.md", "project-types/api-service.md"}
    if any(t in infra_templates for t in active_templates) and not profile.deployment:
        deploy = Prompt.ask(
            "  Deployment target",
            choices=["local", "docker", "kubernetes", "serverless", "other"],
            default="local",
        )
        profile.deployment = deploy if deploy != "other" else Prompt.ask("    Specify")

    # Additional context
    context = Prompt.ask(
        "  Additional context [dim](team conventions, constraints, etc. — optional)[/dim]",
        default="",
    )
    if context.strip():
        profile.context = context.strip()

    return profile


def _update_gitignore(root: Path) -> None:
    gitignore = root / ".gitignore"
    entries = [
        "# Byakugan (local, not committed)",
        ".byakugan/",
        "CLAUDE.md",
        ".claude/settings.local.json",
    ]
    if gitignore.exists():
        existing = gitignore.read_text(encoding="utf-8")
        new_entries = [e for e in entries if e not in existing]
        if new_entries:
            with gitignore.open("a", encoding="utf-8") as f:
                f.write("\n" + "\n".join(new_entries) + "\n")
    else:
        gitignore.write_text("\n".join(entries) + "\n", encoding="utf-8")
