"""
Core PromptVault operations — save, get, search, list, delete, rename, export, import.
Orchestrates storage (file system), database (SQLite), and versioning (Git).
API surface matches cli.py expectations.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from prompt_stash.config import VaultConfig
from prompt_stash.database import PromptRecord, VaultDatabase
from prompt_stash.storage import PromptStorage
from prompt_stash.utils.fuzzy import fuzzy_find


class PromptVault:

    def __init__(self, config: VaultConfig) -> None:
        self.config = config
        self.storage = PromptStorage(config.prompts_dir)
        self.db = VaultDatabase(config.db_path)

    # ── save ──────────────────────────────────────────────────────
    def save(
        self,
        name: str,
        content: str,
        tags: list[str] | None = None,
        model: str = "",
        description: str = "",
    ) -> dict:
        """Save (or update) a prompt. Returns the resulting record dict."""
        # Clean HTML entities (like &#x20;) from input
        content = html.unescape(content)
        existing = self.db.get(name)
        now = datetime.now().isoformat()
        version = (existing["version"] + 1) if existing else 1

        record = PromptRecord(
            name=name,
            description=description,
            tags=tags or [],
            model=model or self.config.default_model or "",
            created=existing["created"] if existing else now,
            updated=now,
            uses=existing["uses"] if existing else 0,
            version=version,
            content_preview=content[:200],
        )

        # Write .md file
        self.storage.write(name, content, {
            "description": description,
            "tags": tags or [],
            "model": record.model,
            "created": record.created,
            "uses": record.uses,
            "version": version,
        })

        # Index in SQLite
        self.db.upsert(record)

        # Git commit
        action = "update" if existing else "add"
        self.storage.commit(name, action)

        return {
            "name": name,
            "version": version,
            "tags": tags or [],
            "model": record.model,
        }

    # ── get ────────────────────────────────────────────────────────
    def get(self, name: str) -> dict | None:
        """Retrieve a prompt by name, with fuzzy fallback. Returns dict with 'content' key."""
        record = self.db.get(name)

        if not record:
            # Try fuzzy match
            all_names = [r["name"] for r in self.db.all()]
            match = fuzzy_find(name, all_names)
            if match:
                record = self.db.get(match)

        if not record:
            return None

        content = self.storage.read_content(record["name"])
        # Safety: unescape even on retrieval in case existing files have entities
        content = html.unescape(content or "")
        
        tag_list = (record.get("tag_list") or "").split(",")
        tags = [t.strip() for t in tag_list if t.strip()]

        return {
            "name": record["name"],
            "content": content or "",
            "tags": tags,
            "model": record.get("model", ""),
            "version": record.get("version", 1),
            "uses": record.get("uses", 0),
            "description": record.get("description", ""),
            "created": record.get("created", ""),
            "updated": record.get("updated", ""),
        }

    # ── search ────────────────────────────────────────────────────
    def search(
        self,
        query: str = "",
        tag: str | None = None,
        model: str | None = None,
    ) -> list[dict]:
        """Search prompts. Returns list of record dicts."""
        results = self.db.search(query, tag=tag, model=model)
        return [self._enrich(r) for r in results]

    # ── list ──────────────────────────────────────────────────────
    def list(
        self,
        tag: str | None = None,
        model: str | None = None,
    ) -> list[dict]:
        """List all prompts with optional filters."""
        results = self.db.all(tag=tag, model=model)
        return [self._enrich(r) for r in results]

    # ── delete ────────────────────────────────────────────────────
    def delete(self, name: str) -> bool:
        """Delete a prompt. Returns True if deleted, False if not found."""
        existed = self.db.delete(name)
        if existed:
            self.storage.delete(name)
            self.storage.commit(name, "delete")
        return existed

    # ── rename ────────────────────────────────────────────────────
    def rename(self, old_name: str, new_name: str) -> None:
        content = self.storage.read_content(old_name)
        meta = self.storage.read_metadata(old_name) or {}
        self.storage.delete(old_name)
        self.storage.commit(old_name, "delete")
        if content:
            self.save(
                new_name,
                content=content,
                tags=meta.get("tags", []),
                model=meta.get("model", ""),
                description=meta.get("description", ""),
            )
        self.db.delete(old_name)

    # ── add tags ──────────────────────────────────────────────────
    def add_tags(self, name: str, tags: list[str]) -> None:
        record = self.db.get(name)
        if not record:
            return
        existing = set((record.get("tag_list") or "").split(",")) - {""}
        existing.update(t.strip().lower() for t in tags)
        self.db.update_tags(name, list(existing))

    # ── export ────────────────────────────────────────────────────
    def export(self, output: str, fmt: str = "json") -> None:
        """Export all prompts to a file."""
        prompts = self.list()
        for p in prompts:
            content = self.storage.read_content(p["name"])
            p["content"] = content or ""

        path = Path(output)
        if fmt == "json":
            path.write_text(json.dumps(prompts, indent=2, default=str), encoding="utf-8")
        else:
            md_parts = []
            for p in prompts:
                md_parts.append(f"# {p['name']}\n\n{p.get('content', '')}\n")
            path.write_text("\n---\n\n".join(md_parts), encoding="utf-8")

    # ── import ────────────────────────────────────────────────────
    def import_from(self, source: str) -> int:
        """Import prompts from a JSON or markdown file. Returns count imported."""
        path = Path(source)
        text = path.read_text(encoding="utf-8")
        count = 0

        if path.suffix == ".json":
            data = json.loads(text)
            for item in data:
                self.save(
                    name=item.get("name", path.stem),
                    content=item.get("content", ""),
                    tags=item.get("tags", []),
                    model=item.get("model", ""),
                    description=item.get("description", ""),
                )
                count += 1
        else:
            # Single markdown file import
            self.save(name=path.stem, content=text)
            count = 1

        return count

    # ── internal ──────────────────────────────────────────────────
    def _enrich(self, row: dict) -> dict:
        """Normalise a DB row into a clean dict with tags as list."""
        tag_list = (row.get("tag_list") or "").split(",")
        tags = [t.strip() for t in tag_list if t.strip()]
        return {
            "name": row.get("name", ""),
            "tags": tags,
            "model": row.get("model", ""),
            "version": row.get("version", 1),
            "uses": row.get("uses", 0),
            "description": row.get("description", ""),
            "updated": row.get("updated", ""),
            "created": row.get("created", ""),
        }
