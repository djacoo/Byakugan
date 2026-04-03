"""byakugan init — initialize Byakugan in the current project."""
from __future__ import annotations

from pathlib import Path

import questionary
from questionary import Choice, Separator
import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

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
    get_db_path,
)
from byakugan.core.detector import detect, LANGUAGE_TO_TEMPLATE
from byakugan.core.database import init_db, migrate_from_legacy
from byakugan.core.superpowers import is_superpowers_installed

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

    # ── Superpowers detection ─────────────────────────────────────────────
    superpowers_detected = is_superpowers_installed()
    if superpowers_detected:
        console.print("  [green]✓[/green] Superpowers detected")
    else:
        console.print("  [dim]·[/dim] Superpowers not detected")
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
    while not active_templates:
        console.print("[yellow]No templates selected — pick at least one.[/yellow]")
        console.print()
        active_templates = _select_templates(suggested)

    console.print()

    # ── Clarifying questions ───────────────────────────────────────────────────
    profile = _ask_clarifying_questions(profile, active_templates)
    console.print()

    # ── Build config ───────────────────────────────────────────────────────────
    config = ByakuganConfig(
        initialized_at=now_iso(),
        active_templates=active_templates,
        project=profile,
        superpowers_detected=superpowers_detected,
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

        # Copy bundled skills
        skills_dir = byakugan_dir / "skills"
        skills_dir.mkdir(exist_ok=True)
        try:
            from importlib import resources
            for skill_name in ["gitflow-workflow.md", "model-selection.md"]:
                content = resources.files("byakugan.skills").joinpath(skill_name).read_text(encoding="utf-8")
                (skills_dir / skill_name).write_text(content, encoding="utf-8")
        except Exception:
            pass

        # Save config
        save_config(config, root)

        # Generate CLAUDE.md
        claude_md.write(config, root)

        # Install hooks
        hooks.install_hooks(root)

        # Init database (with migration from legacy if needed)
        db_path = get_db_path(root)
        old_db = byakugan_dir / "memory.db"
        if old_db.exists():
            migrate_from_legacy(old_db, db_path)
            console.print("  [green]✓[/green] Migrated memory.db → byakugan.db")
        else:
            init_db(db_path)

        # Update .gitignore
        _update_gitignore(root)

    # ── Done ───────────────────────────────────────────────────────────────────
    console.print("[bold green]✓[/bold green] Byakugan initialized.")
    console.print()
    console.print("  [dim]Guidelines:[/dim]   .byakugan/")
    console.print("  [dim]Entry point:[/dim]  CLAUDE.md")
    console.print("  [dim]Database:[/dim]    .byakugan/byakugan.db")
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


_CATEGORY_LABELS = {
    "languages":     "Languages",
    "project-types": "Project Types",
    "specialized":   "Specialized",
}

_TEMPLATE_DESC = {
    # Languages
    "languages/python.md":      "Python",
    "languages/typescript.md":  "TypeScript",
    "languages/javascript.md":  "JavaScript",
    "languages/rust.md":        "Rust",
    "languages/go.md":          "Go",
    "languages/java.md":        "Java",
    "languages/kotlin.md":      "Kotlin",
    "languages/swift.md":       "Swift",
    "languages/ruby.md":        "Ruby",
    "languages/php.md":         "PHP",
    "languages/c.md":           "C",
    "languages/cpp.md":         "C++",
    "languages/css.md":         "CSS / SCSS",
    # Project types
    "project-types/web-backend.md":           "Web Backend  (REST / GraphQL API server)",
    "project-types/web-frontend.md":          "Web Frontend  (React / Vue / Svelte ...)",
    "project-types/fullstack-web.md":         "Fullstack Web  (Next.js / Nuxt / Remix ...)",
    "project-types/api-service.md":           "API Service  (standalone microservice)",
    "project-types/ml-project.md":            "ML Project  (training, notebooks, data)",
    "project-types/llm-project.md":           "LLM Project  (prompts, agents, RAG)",
    "project-types/library-sdk.md":           "Library / SDK  (published package)",
    "project-types/cli-tool.md":              "CLI Tool  (command-line application)",
    "project-types/mobile-app.md":            "Mobile App  (iOS / Android)",
    "project-types/desktop-app.md":           "Desktop App  (Electron / native)",
    "project-types/data-engineering.md":      "Data Engineering  (pipelines, ETL)",
    "project-types/devops-infrastructure.md": "DevOps / Infrastructure  (Docker, k8s, Terraform)",
    # Specialized
    "specialized/security-check.md":          "Security  (OWASP, auth, secrets)",
    "specialized/testing-strategy.md":        "Testing  (unit, integration, coverage)",
    "specialized/database-design.md":         "Database Design  (schema, migrations, queries)",
    "specialized/api-design.md":              "API Design  (REST conventions, versioning)",
    "specialized/devops-infrastructure.md":   "DevOps  (CI/CD, containers, deployments)",
    "specialized/refactoring.md":             "Refactoring  (safe change strategies)",
    "specialized/code-simplification.md":     "Code Simplification  (reduce complexity)",
    "specialized/performance-optimization.md":"Performance  (profiling, caching, tuning)",
    "specialized/gitflow-workflow.md":        "Git Workflow  (branches, commits, PRs)",
    "specialized/debugging.md":              "Debugging  (systematic diagnosis)",
    "specialized/code-review.md":            "Code Review  (what to check, severity)",
    "specialized/ai-usage-policy.md":        "AI Usage Policy  (LLM guardrails)",
}


def _select_templates(suggested: list[str]) -> list[str]:
    """Interactive checkbox template picker — arrows to move, space to toggle, enter to confirm."""
    all_templates = adapter.list_bundled_templates()
    suggested_set = set(suggested)

    console.print("Template selection:", style="bold")
    if suggested_set:
        console.print("  [dim]Auto-detected templates are pre-selected (·). Toggle with space.[/dim]")
    else:
        console.print("  [dim]Nothing detected automatically — select what you plan to build.[/dim]")
    console.print()

    choices: list = []
    for cat, names in all_templates.items():
        label = _CATEGORY_LABELS.get(cat, cat)
        choices.append(Separator(f"  ── {label} {'─' * (34 - len(label))}"))
        for name in names:
            key = f"{cat}/{name}"
            display = _TEMPLATE_DESC.get(key, key)
            choices.append(Choice(title=display, value=key, checked=(key in suggested_set)))

    style = questionary.Style([
        ("separator",     "fg:#555555"),
        ("checkbox",      "fg:#00afd7"),
        ("checked",       "fg:#00d7af bold"),
        ("pointer",       "fg:#ff8c00 bold"),
        ("highlighted",   "fg:#ffffff bold"),
        ("selected",      "fg:#00d7af"),
        ("instruction",   "fg:#555555 italic"),
        ("question",      "fg:#00afd7 bold"),
        ("answer",        "fg:#00d7af bold"),
    ])

    result = questionary.checkbox(
        "Choose guidelines:",
        choices=choices,
        instruction="  (↑↓ move · space toggle · enter confirm · ctrl+a all · ctrl+r none)",
        style=style,
        use_arrow_keys=True,
        use_jk_keys=False,
    ).ask()

    if result is None:
        # User hit ctrl+c
        raise typer.Exit(0)

    return result


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
        ".claude/remember/",
        ".remember/",
        "docs/superpowers/",
    ]
    if gitignore.exists():
        existing = gitignore.read_text(encoding="utf-8")
        new_entries = [e for e in entries if e not in existing]
        if new_entries:
            with gitignore.open("a", encoding="utf-8") as f:
                f.write("\n" + "\n".join(new_entries) + "\n")
    else:
        gitignore.write_text("\n".join(entries) + "\n", encoding="utf-8")
