"""Haiku compression pipeline for session events.

Compresses raw tool-use events into summaries using Claude Haiku.
All compression runs in background subprocesses — never blocks hooks.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from byakugan.core.database import (
    get_pending_event_count,
    get_pending_events,
    save_summary,
    delete_events_by_ids,
)

logger = logging.getLogger(__name__)

COMPRESSION_THRESHOLD = 50
HAIKU_MODEL = "claude-haiku-4-5-20251001"

COMPRESSION_PROMPT = """Summarize the following developer tool-use events into a concise paragraph.
Focus on: what files were touched, what kind of work was done, key commands run.
Keep it under 150 words. Be factual, not interpretive.

Events:
{events}"""


def should_compress(db_path: Path) -> bool:
    """Check if compression threshold is met."""
    return get_pending_event_count(db_path) >= COMPRESSION_THRESHOLD


def format_events_for_compression(events: list[dict]) -> str:
    """Format raw events into text for the Haiku prompt."""
    lines = []
    for e in events:
        parts = [e["captured_at"], e["tool_name"]]
        if e.get("file_path"):
            parts.append(e["file_path"])
        if e.get("tool_input_snapshot"):
            try:
                snap = json.loads(e["tool_input_snapshot"])
                if cmd := snap.get("command"):
                    parts.append(f"cmd={cmd[:80]}")
            except (json.JSONDecodeError, TypeError):
                pass
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def _call_haiku(prompt: str) -> str:
    """Call Claude Haiku via the anthropic SDK. Raises on failure."""
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def compress_events(db_path: Path) -> bool:
    """Compress pending events into an hourly summary. Returns True if compression was performed."""
    events = get_pending_events(db_path)
    if len(events) < COMPRESSION_THRESHOLD:
        return False

    text = format_events_for_compression(events)
    prompt = COMPRESSION_PROMPT.format(events=text)

    try:
        summary_text = _call_haiku(prompt)
    except Exception as e:
        logger.warning("Haiku compression failed: %s", e)
        return False

    session_ids = list({e["session_id"] for e in events})
    session_id = session_ids[0] if len(session_ids) == 1 else ",".join(sorted(session_ids))

    save_summary(
        db_path,
        session_id=session_id,
        period="hourly",
        content=summary_text,
        source_event_count=len(events),
    )
    delete_events_by_ids(db_path, [e["id"] for e in events])
    return True


def spawn_background_compression(db_path: Path) -> None:
    """Spawn a background subprocess to run compression. Non-blocking."""
    subprocess.Popen(
        [sys.executable, "-m", "byakugan.core.compression", str(db_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


if __name__ == "__main__":
    """Entry point for background compression subprocess."""
    if len(sys.argv) != 2:
        sys.exit(1)
    db_path = Path(sys.argv[1])
    if db_path.exists():
        compress_events(db_path)
