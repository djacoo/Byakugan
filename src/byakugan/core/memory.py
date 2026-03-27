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
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at       TEXT    NOT NULL,
    type             TEXT    NOT NULL,
    content          TEXT    NOT NULL,
    context          TEXT,
    tags             TEXT,
    importance       INTEGER NOT NULL DEFAULT 3,
    last_surfaced_at TEXT,
    surface_count    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    summary     TEXT
);

CREATE INDEX IF NOT EXISTS idx_memories_type       ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memories_surfaced   ON memories(last_surfaced_at DESC);
"""

VALID_TYPES = {"correction", "decision", "preference", "pattern", "note"}

TYPE_PREFIXES = {
    "correction:": "correction",
    "decision:": "decision",
    "preference:": "preference",
    "pattern:": "pattern",
    "note:": "note",
}

# Keywords that auto-elevate importance
HIGH_IMPORTANCE_KEYWORDS = {"never", "always", "critical", "security", "vulnerability", "breaking", "must", "required"}
LOW_IMPORTANCE_KEYWORDS  = {"prefer", "try", "consider", "might", "optional", "sometimes"}

# Jaccard similarity threshold for deduplication
DUPLICATE_THRESHOLD = 0.70


@dataclass
class Memory:
    id: int
    created_at: str
    type: str
    content: str
    context: dict
    tags: list[str]
    importance: int
    last_surfaced_at: str | None = None
    surface_count: int = 0

    def short(self) -> str:
        return self.content[:120] + ("…" if len(self.content) > 120 else "")


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    # Add new columns to existing databases (migration)
    _migrate(conn)
    conn.commit()
    # Performance settings
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Add new columns to existing databases without breaking them."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(memories)").fetchall()}
    if "last_surfaced_at" not in cols:
        conn.execute("ALTER TABLE memories ADD COLUMN last_surfaced_at TEXT")
    if "surface_count" not in cols:
        conn.execute("ALTER TABLE memories ADD COLUMN surface_count INTEGER NOT NULL DEFAULT 0")


def init_db(db_path: Path) -> None:
    conn = _connect(db_path)
    conn.close()


def infer_type(content: str) -> str:
    lower = content.lower().strip()
    for prefix, t in TYPE_PREFIXES.items():
        if lower.startswith(prefix):
            return t
    return "note"


def infer_importance(content: str, base: int = 3) -> int:
    """Auto-adjust importance based on keywords in the content."""
    lower = content.lower()
    if any(kw in lower for kw in HIGH_IMPORTANCE_KEYWORDS):
        return min(5, base + 1)
    if any(kw in lower for kw in LOW_IMPORTANCE_KEYWORDS):
        return max(1, base - 1)
    return base


def _extract_tags(content: str, context: dict) -> list[str]:
    tags: list[str] = []

    if context.get("language"):
        tags.append(context["language"])
    if context.get("file"):
        path = Path(context["file"])
        tags.append(path.suffix.lstrip("."))
        # Extract meaningful path segments
        for part in path.parts[-3:]:
            stem = Path(part).stem.lower()
            if stem and stem not in {"src", "lib", "app", "main", "index", "mod", "test"}:
                tags.append(stem)

    # Backtick-quoted terms (code identifiers)
    tags += re.findall(r"`([^`]{2,40})`", content)[:4]

    # Extract def/class/func names
    for m in re.finditer(r"\b(?:def|class|func|fn|function)\s+(\w+)", content):
        tags.append(m.group(1).lower())

    # Deduplicate, lowercase, filter noise
    seen: set[str] = set()
    result: list[str] = []
    for t in tags:
        t = t.lower().strip()
        if t and t not in seen and len(t) > 1:
            seen.add(t)
            result.append(t)

    return result[:10]


def _jaccard(a: str, b: str) -> float:
    words_a = set(re.findall(r"\w+", a.lower()))
    words_b = set(re.findall(r"\w+", b.lower()))
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def is_duplicate(db_path: Path, content: str) -> Optional[int]:
    """
    Return the ID of a near-duplicate memory if one exists, else None.
    Uses Jaccard similarity on word sets.
    """
    if not db_path.exists():
        return None
    conn = _connect(db_path)
    rows = conn.execute("SELECT id, content FROM memories ORDER BY created_at DESC LIMIT 200").fetchall()
    conn.close()
    for row in rows:
        if _jaccard(content, row["content"]) >= DUPLICATE_THRESHOLD:
            return row["id"]
    return None


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

    # Auto-adjust importance from content
    importance = infer_importance(content, importance)

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


def update_surfaced(db_path: Path, memory_ids: list[int]) -> None:
    """Record that these memories were surfaced to the user (for scoring and decay)."""
    if not db_path.exists() or not memory_ids:
        return
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect(db_path)
    conn.executemany(
        """UPDATE memories
           SET last_surfaced_at = ?, surface_count = surface_count + 1
           WHERE id = ?""",
        [(now, mid) for mid in memory_ids],
    )
    conn.commit()
    conn.close()


def query_relevant(
    db_path: Path,
    language: str | None = None,
    file_path: str | None = None,
    keywords: list[str] | None = None,
    operation: str | None = None,
    limit: int = 4,
) -> list[Memory]:
    """
    Return the most relevant memories for the given context.

    Scoring: base importance + language/file/keyword/recency bonuses.
    Fetches top candidates then re-ranks in Python for precision.
    """
    if not db_path.exists():
        return []

    conn = _connect(db_path)

    # Fetch a broader candidate set — we'll re-rank in Python
    fetch_limit = min(50, limit * 8)

    # Build lightweight WHERE to filter clearly irrelevant entries
    conditions: list[str] = []
    params: list = []

    if language:
        conditions.append("(tags LIKE ? OR context LIKE ?)")
        params.extend([f"%{language}%", f"%{language}%"])

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT * FROM memories
        {where}
        ORDER BY importance DESC, created_at DESC
        LIMIT ?
    """
    params.append(fetch_limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    memories = [
        Memory(
            id=r["id"],
            created_at=r["created_at"],
            type=r["type"],
            content=r["content"],
            context=json.loads(r["context"] or "{}"),
            tags=json.loads(r["tags"] or "[]"),
            importance=r["importance"],
            last_surfaced_at=r["last_surfaced_at"],
            surface_count=r["surface_count"],
        )
        for r in rows
    ]

    # Re-rank with composite scoring
    scored = [(_score(m, language, file_path, keywords, operation), m) for m in memories]
    scored.sort(key=lambda x: x[0], reverse=True)

    return [m for _, m in scored[:limit]]


def _score(
    m: Memory,
    language: str | None,
    file_path: str | None,
    keywords: list[str] | None,
    operation: str | None,
) -> float:
    score = float(m.importance) * 10.0

    # Language match
    if language and language in m.tags:
        score += 15.0

    # File path match — same directory or file stem
    if file_path:
        fp_lower = file_path.lower()
        for tag in m.tags:
            if len(tag) > 3 and tag in fp_lower:
                score += 12.0
                break
        # Exact file match in context
        if m.context.get("file", "").lower() in fp_lower:
            score += 20.0

    # Keyword hits in content
    if keywords:
        hits = sum(1 for kw in keywords if kw.lower() in m.content.lower())
        score += hits * 8.0

    # Operation type match (corrections most relevant for edits)
    if operation in ("Edit", "Write", "MultiEdit") and m.type == "correction":
        score += 10.0
    if operation == "Bash" and m.type in ("pattern", "preference"):
        score += 5.0

    # Recency bonus (decays over 90 days)
    try:
        age_days = (
            datetime.now(timezone.utc)
            - datetime.fromisoformat(m.created_at)
        ).days
        recency = max(0.0, 1.0 - age_days / 90.0)
        score += recency * 8.0
    except Exception:
        pass

    # High-importance memories that haven't been surfaced recently get a bump
    if m.last_surfaced_at is None and m.importance >= 4:
        score += 6.0

    return score


def search(db_path: Path, query: str, limit: int = 20) -> list[Memory]:
    """Full-text search across memory content and tags."""
    if not db_path.exists():
        return []

    terms = query.lower().split()
    if not terms:
        return get_all(db_path, limit=limit)

    conn = _connect(db_path)
    conditions = " AND ".join(["(content LIKE ? OR tags LIKE ?)"] * len(terms))
    params = []
    for term in terms:
        params.extend([f"%{term}%", f"%{term}%"])
    params.append(limit)

    rows = conn.execute(
        f"SELECT * FROM memories WHERE {conditions} ORDER BY importance DESC, created_at DESC LIMIT ?",
        params,
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
            last_surfaced_at=r["last_surfaced_at"],
            surface_count=r["surface_count"],
        )
        for r in rows
    ]


def apply_decay(db_path: Path, days_threshold: int = 90) -> int:
    """
    Decay importance by 1 for memories not surfaced in `days_threshold` days
    that are older than that threshold. Returns number of memories decayed.
    """
    if not db_path.exists():
        return 0
    conn = _connect(db_path)
    cur = conn.execute(
        """UPDATE memories
           SET importance = MAX(1, importance - 1)
           WHERE importance > 1
             AND created_at < datetime('now', ?)
             AND (last_surfaced_at IS NULL OR last_surfaced_at < datetime('now', ?))""",
        (f"-{days_threshold} days", f"-{days_threshold} days"),
    )
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected


def prune(db_path: Path, days_threshold: int = 90) -> int:
    """Remove importance-1 memories older than days_threshold. Returns count removed."""
    if not db_path.exists():
        return 0
    conn = _connect(db_path)
    cur = conn.execute(
        """DELETE FROM memories
           WHERE importance = 1
             AND created_at < datetime('now', ?)""",
        (f"-{days_threshold} days",),
    )
    conn.commit()
    removed = cur.rowcount
    conn.close()
    return removed


def get_all(db_path: Path, limit: int = 50) -> list[Memory]:
    if not db_path.exists():
        return []
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM memories ORDER BY importance DESC, created_at DESC LIMIT ?", (limit,)
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
            last_surfaced_at=r["last_surfaced_at"],
            surface_count=r["surface_count"],
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
