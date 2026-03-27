"""SQLite-backed project memory — stores corrections, decisions, patterns, preferences."""
from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT    NOT NULL,
    type        TEXT    NOT NULL,
    content     TEXT    NOT NULL,
    context     TEXT,
    tags        TEXT,
    importance  INTEGER NOT NULL DEFAULT 3
);

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    summary     TEXT
);

CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
"""

VALID_TYPES = {"correction", "decision", "preference", "pattern", "note"}

# Infer type from prefix in content
TYPE_PREFIXES = {
    "correction:": "correction",
    "decision:": "decision",
    "preference:": "preference",
    "pattern:": "pattern",
    "note:": "note",
}


@dataclass
class Memory:
    id: int
    created_at: str
    type: str
    content: str
    context: dict
    tags: list[str]
    importance: int

    def short(self) -> str:
        return self.content[:120] + ("…" if len(self.content) > 120 else "")


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def init_db(db_path: Path) -> None:
    conn = _connect(db_path)
    conn.close()


def infer_type(content: str) -> str:
    lower = content.lower().strip()
    for prefix, t in TYPE_PREFIXES.items():
        if lower.startswith(prefix):
            return t
    return "note"


def _extract_tags(content: str, context: dict) -> list[str]:
    tags = []
    if context.get("language"):
        tags.append(context["language"])
    if context.get("file"):
        path = Path(context["file"])
        tags.append(path.suffix.lstrip("."))
    # Extract quoted terms as potential tags
    tags += re.findall(r"`([^`]+)`", content)[:3]
    return [t.lower() for t in tags if t]


def store(
    db_path: Path,
    content: str,
    memory_type: str | None = None,
    context: dict | None = None,
    importance: int = 3,
) -> int:
    if memory_type is None:
        memory_type = infer_type(content)
    if memory_type not in VALID_TYPES:
        memory_type = "note"

    ctx = context or {}
    tags = _extract_tags(content, ctx)

    conn = _connect(db_path)
    cursor = conn.execute(
        """INSERT INTO memories (created_at, type, content, context, tags, importance)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            datetime.now(timezone.utc).isoformat(),
            memory_type,
            content,
            json.dumps(ctx),
            json.dumps(tags),
            max(1, min(5, importance)),
        ),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def query_relevant(
    db_path: Path,
    language: str | None = None,
    file_path: str | None = None,
    keywords: list[str] | None = None,
    limit: int = 4,
) -> list[Memory]:
    """Return the most relevant memories for the given context."""
    if not db_path.exists():
        return []

    conn = _connect(db_path)

    conditions: list[str] = []
    params: list = []

    # Filter by language tag
    if language:
        conditions.append("(tags LIKE ? OR context LIKE ?)")
        params.extend([f"%{language}%", f"%{language}%"])

    # Filter by file extension
    if file_path:
        ext = Path(file_path).suffix.lstrip(".")
        if ext:
            conditions.append("(tags LIKE ? OR content LIKE ?)")
            params.extend([f"%{ext}%", f"%{ext}%"])

    # Filter by keywords
    if keywords:
        kw_conditions = " OR ".join(["content LIKE ?"] * len(keywords))
        conditions.append(f"({kw_conditions})")
        params.extend([f"%{kw}%" for kw in keywords])

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT * FROM memories
        {where}
        ORDER BY importance DESC, created_at DESC
        LIMIT ?
    """
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return [
        Memory(
            id=r["id"],
            created_at=r["created_at"],
            type=r["type"],
            content=r["content"],
            context=json.loads(r["context"] or "{}"),
            tags=json.loads(r["tags"] or "[]"),
            importance=r["importance"],
        )
        for r in rows
    ]


def get_all(db_path: Path, limit: int = 50) -> list[Memory]:
    if not db_path.exists():
        return []
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [
        Memory(
            id=r["id"],
            created_at=r["created_at"],
            type=r["type"],
            content=r["content"],
            context=json.loads(r["context"] or "{}"),
            tags=json.loads(r["tags"] or "[]"),
            importance=r["importance"],
        )
        for r in rows
    ]


def count(db_path: Path) -> int:
    if not db_path.exists():
        return 0
    conn = _connect(db_path)
    n = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    conn.close()
    return n


def delete(db_path: Path, memory_id: int) -> bool:
    if not db_path.exists():
        return False
    conn = _connect(db_path)
    cur = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0
