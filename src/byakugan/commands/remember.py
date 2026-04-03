"""byakugan remember — store a memory in the project's knowledge base."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from byakugan.core.config import find_byakugan_root, get_db_path, load_config
from byakugan.core.memory import (
    TYPE_PREFIXES,
    infer_importance,
    is_duplicate,
    store,
)

console = Console()

# Map file extension → language name (for context tagging)
_EXT_TO_LANG = {
    ".py": "python", ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".rs": "rust", ".go": "go", ".java": "java",
    ".kt": "kotlin", ".swift": "swift", ".rb": "ruby",
    ".php": "php", ".c": "c", ".cpp": "cpp", ".cc": "cpp",
}


def _infer_context(byakugan_root: Path) -> dict:
    """Infer language and project context from the stored profile."""
    ctx: dict = {}
    try:
        config = load_config(byakugan_root)
        profile = config.project
        if profile.languages:
            ctx["language"] = profile.languages[0]
    except Exception:
        pass
    return ctx


def run(note: str, importance: int = 3, file: str | None = None) -> None:
    root = Path.cwd()
    byakugan_root = find_byakugan_root(root)
    if byakugan_root is None:
        console.print("[red]No Byakugan setup found. Run [bold]byakugan init[/bold] first.[/red]")
        raise typer.Exit(1)

    db_path = get_db_path(byakugan_root)
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

    # Build context: use supplied file or infer from project profile
    context = _infer_context(byakugan_root)
    if file:
        context["file"] = file
        p = Path(file)
        lang = _EXT_TO_LANG.get(p.suffix.lower())
        if lang:
            context["language"] = lang

    # Deduplication check
    dup_id = is_duplicate(db_path, content)
    if dup_id is not None:
        console.print(f"[yellow]⚠ A similar memory already exists (ID {dup_id}).[/yellow]")
        console.print(f"  Run [bold]byakugan memories list[/bold] to review it.")
        confirmed = Confirm.ask("Store anyway?", default=False)
        if not confirmed:
            console.print("Not stored.")
            return

    mem_id = store(db_path, content=content, memory_type=memory_type, context=context, importance=final_importance)

    imp_note = f" (importance: {final_importance}/5)" if final_importance != 3 else ""
    lang_note = f" [{context['language']}]" if context.get("language") else ""
    console.print(
        f"[bold green]✓[/bold green] Stored [{memory_type}]{lang_note}{imp_note} (ID {mem_id}): "
        f"{content[:80]}{'…' if len(content) > 80 else ''}"
    )
