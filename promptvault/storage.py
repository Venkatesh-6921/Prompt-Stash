"""
Prompt file storage — .md files with YAML frontmatter + Git commits.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class PromptStorage:
    """Manages prompt markdown files and their Git history."""

    def __init__(self, prompts_dir: Path) -> None:
        self.prompts_dir = prompts_dir
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    # ── paths ─────────────────────────────────────────────────────
    def _path(self, name: str) -> Path:
        safe = re.sub(r"[^\w\-]", "-", name)
        return self.prompts_dir / f"{safe}.md"

    # ── write ─────────────────────────────────────────────────────
    def write(self, name: str, content: str, meta: dict[str, Any]) -> Path:
        """Write a prompt to disk as a .md file with YAML frontmatter."""
        frontmatter = {
            "name": name,
            "description": meta.get("description", ""),
            "tags": meta.get("tags", []),
            "model": meta.get("model", ""),
            "created": meta.get("created", datetime.now().isoformat()),
            "updated": datetime.now().isoformat(),
            "uses": meta.get("uses", 0),
            "version": meta.get("version", 1),
        }
        header = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        text = f"---\n{header}---\n\n{content}\n"
        path = self._path(name)
        path.write_text(text, encoding="utf-8")
        return path

    # ── read ──────────────────────────────────────────────────────
    def read_content(self, name: str) -> str | None:
        """Return the body text (below frontmatter) of a prompt file."""
        path = self._path(name)
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8")
        return self._split(raw)[1]

    def read_metadata(self, name: str) -> dict[str, Any] | None:
        """Parse YAML frontmatter and return as dict."""
        path = self._path(name)
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8")
        fm_str = self._split(raw)[0]
        if not fm_str:
            return {}
        return yaml.safe_load(fm_str) or {}

    # ── delete ────────────────────────────────────────────────────
    def delete(self, name: str) -> None:
        path = self._path(name)
        if path.exists():
            path.unlink()

    # ── rename ────────────────────────────────────────────────────
    def rename(self, old_name: str, new_name: str) -> None:
        old_path = self._path(old_name)
        new_path = self._path(new_name)
        if old_path.exists():
            old_path.rename(new_path)

    # ── exists ────────────────────────────────────────────────────
    def exists(self, name: str) -> bool:
        return self._path(name).exists()

    # ── git commit ────────────────────────────────────────────────
    def commit(self, name: str, action: str = "update") -> None:
        """Stage the prompt file and commit."""
        try:
            from git import Repo
            repo = Repo(self.prompts_dir)
            path = self._path(name)
            rel = path.relative_to(self.prompts_dir)
            if path.exists():
                repo.index.add([str(rel)])
            else:
                try:
                    repo.index.remove([str(rel)])
                except Exception:
                    pass
            repo.index.commit(f"{action}: {name}")
        except Exception:
            pass  # Git unavailable — degrade gracefully

    # ── internal ──────────────────────────────────────────────────
    @staticmethod
    def _split(raw: str) -> tuple[str, str]:
        """Split a markdown file into (frontmatter_yaml, body)."""
        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                return parts[1].strip(), parts[2].strip()
        return "", raw.strip()
