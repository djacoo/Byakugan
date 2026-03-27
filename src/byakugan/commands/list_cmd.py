"""byakugan list — list all available bundled templates."""
from __future__ import annotations

from rich.console import Console
from rich.table import Table

from byakugan.core.adapter import list_bundled_templates, template_display_name

console = Console()

CATEGORY_LABELS = {
    "languages": "Languages",
    "project-types": "Project Types",
    "specialized": "Specialized",
}


def run() -> None:
    all_templates = list_bundled_templates()

    console.print()
    console.print("[bold cyan]◈ Byakugan[/bold cyan] — available templates")
    console.print()

    for category, names in all_templates.items():
        if not names:
            continue
        label = CATEGORY_LABELS.get(category, category)
        console.print(f"[bold]{label}[/bold]")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="cyan", width=40)
        table.add_column(style="dim")

        for name in names:
            path = f"{category}/{name}"
            table.add_row(path, template_display_name(path))

        console.print(table)
        console.print()
