"""
SQLite database for PromptVault.
Handles metadata, full-text search, tags, usage statistics, version tracking.
The .md files in prompts/ are the source of truth for content.
SQLite is the index — fast search + metadata without parsing .md files every time.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class PromptRecord:
    name: str
    description: str
    tags: list[str]
    model: str | None
    created: str
    updated: str
    uses: int
    version: int
    content_preview: str  # First 200 chars of prompt body


SCHEMA = """
CREATE TABLE IF NOT EXISTS prompts (
    name            TEXT PRIMARY KEY,
    description     TEXT DEFAULT '',
    model           TEXT DEFAULT '',
    created         TEXT NOT NULL,
    updated         TEXT NOT NULL,
    uses            INTEGER DEFAULT 0,
    version         INTEGER DEFAULT 1,
    content_preview TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS tags (
    prompt_name     TEXT NOT NULL REFERENCES prompts(name) ON DELETE CASCADE,
    tag             TEXT NOT NULL,
    PRIMARY KEY (prompt_name, tag)
);

-- Full-text search index on name, description, and content preview
CREATE VIRTUAL TABLE IF NOT EXISTS prompts_fts USING fts5(
    name,
    description,
    content_preview,
    content='prompts',
    content_rowid='rowid'
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS prompts_ai AFTER INSERT ON prompts BEGIN
    INSERT INTO prompts_fts(rowid, name, description, content_preview)
    VALUES (new.rowid, new.name, new.description, new.content_preview);
END;

CREATE TRIGGER IF NOT EXISTS prompts_ad AFTER DELETE ON prompts BEGIN
    INSERT INTO prompts_fts(prompts_fts, rowid, name, description, content_preview)
    VALUES ('delete', old.rowid, old.name, old.description, old.content_preview);
END;

CREATE TRIGGER IF NOT EXISTS prompts_au AFTER UPDATE ON prompts BEGIN
    INSERT INTO prompts_fts(prompts_fts, rowid, name, description, content_preview)
    VALUES ('delete', old.rowid, old.name, old.description, old.content_preview);
    INSERT INTO prompts_fts(rowid, name, description, content_preview)
    VALUES (new.rowid, new.name, new.description, new.content_preview);
END;
"""


class VaultDatabase:

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ── upsert ────────────────────────────────────────────────────
    def upsert(self, record: PromptRecord) -> None:
        now = datetime.now().isoformat()
        self.conn.execute("""
            INSERT INTO prompts (name, description, model, created, updated, uses, version, content_preview)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                description     = excluded.description,
                model           = excluded.model,
                updated         = ?,
                version         = version + 1,
                content_preview = excluded.content_preview
        """, (
            record.name, record.description, record.model or "",
            record.created, now, record.uses, record.version,
            record.content_preview, now
        ))
        # Refresh tags
        self.conn.execute("DELETE FROM tags WHERE prompt_name = ?", (record.name,))
        for tag in record.tags:
            self.conn.execute(
                "INSERT OR IGNORE INTO tags (prompt_name, tag) VALUES (?, ?)",
                (record.name, tag.strip().lower())
            )
        self.conn.commit()

    # ── increment uses ────────────────────────────────────────────
    def increment_uses(self, name: str) -> None:
        self.conn.execute(
            "UPDATE prompts SET uses = uses + 1 WHERE name = ?", (name,)
        )
        self.conn.commit()

    # ── search ────────────────────────────────────────────────────
    def search(self, query: str, tag: str | None = None, model: str | None = None) -> list[dict]:
        if query:
            rows = self.conn.execute("""
                SELECT p.*, GROUP_CONCAT(t.tag, ',') as tag_list
                FROM prompts_fts fts
                JOIN prompts p ON p.rowid = fts.rowid
                LEFT JOIN tags t ON t.prompt_name = p.name
                WHERE prompts_fts MATCH ?
                GROUP BY p.name
                ORDER BY rank
            """, (query,)).fetchall()
        else:
            rows = self.conn.execute("""
                SELECT p.*, GROUP_CONCAT(t.tag, ',') as tag_list
                FROM prompts p
                LEFT JOIN tags t ON t.prompt_name = p.name
                GROUP BY p.name
                ORDER BY p.updated DESC
            """).fetchall()

        results = [dict(r) for r in rows]

        if tag:
            results = [r for r in results if tag.lower() in (r.get("tag_list") or "").split(",")]
        if model:
            results = [r for r in results if r.get("model", "").lower() == model.lower()]

        return results

    # ── get ────────────────────────────────────────────────────────
    def get(self, name: str) -> dict | None:
        row = self.conn.execute("""
            SELECT p.*, GROUP_CONCAT(t.tag, ',') as tag_list
            FROM prompts p
            LEFT JOIN tags t ON t.prompt_name = p.name
            WHERE p.name = ?
            GROUP BY p.name
        """, (name,)).fetchone()
        return dict(row) if row else None

    # ── delete ────────────────────────────────────────────────────
    def delete(self, name: str) -> bool:
        cursor = self.conn.execute("DELETE FROM prompts WHERE name = ?", (name,))
        self.conn.commit()
        return cursor.rowcount > 0

    # ── all ────────────────────────────────────────────────────────
    def all(self, tag: str | None = None, model: str | None = None) -> list[dict]:
        return self.search("", tag=tag, model=model)

    # ── rename ────────────────────────────────────────────────────
    def rename(self, old_name: str, new_name: str) -> None:
        # Disable FK checks temporarily so we can update both tables atomically
        self.conn.execute("PRAGMA foreign_keys = OFF")
        self.conn.execute("UPDATE tags SET prompt_name = ? WHERE prompt_name = ?", (new_name, old_name))
        self.conn.execute("UPDATE prompts SET name = ? WHERE name = ?", (new_name, old_name))
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.commit()

    # ── update tags ───────────────────────────────────────────────
    def update_tags(self, name: str, tags: list[str]) -> None:
        self.conn.execute("DELETE FROM tags WHERE prompt_name = ?", (name,))
        for tag in tags:
            self.conn.execute(
                "INSERT OR IGNORE INTO tags (prompt_name, tag) VALUES (?, ?)",
                (name, tag.strip().lower())
            )
        self.conn.commit()

    # ── close ─────────────────────────────────────────────────────
    def close(self) -> None:
        self.conn.close()
