"""
Git-based version history for individual prompts.
Uses GitPython to provide log, diff, and rollback per prompt.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text

console = Console()


class PromptVersioning:
    """Version control operations on the prompts Git repo."""

    def __init__(self, config: Any) -> None:
        self.prompts_dir = config.prompts_dir
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            from git import Repo
            self._repo = Repo(self.prompts_dir)
        return self._repo

    def _filename(self, name: str) -> str:
        safe = re.sub(r"[^\w\-]", "-", name)
        return f"{safe}.md"

    # ── log ───────────────────────────────────────────────────────
    def log(self, name: str) -> list[dict]:
        """Return version history entries for a prompt."""
        filename = self._filename(name)
        entries: list[dict] = []
        try:
            commits = list(self.repo.iter_commits(paths=filename))
            for i, commit in enumerate(reversed(commits), start=1):
                entries.append({
                    "version": i,
                    "hash": commit.hexsha,
                    "message": commit.message.strip(),
                    "date": commit.committed_datetime.isoformat(),
                })
        except Exception:
            pass
        return entries

    # ── diff ──────────────────────────────────────────────────────
    def diff(self, name: str, v_from: str | None = None, v_to: str | None = None) -> None:
        """Print a rich diff between two versions of a prompt."""
        filename = self._filename(name)
        try:
            commits = list(self.repo.iter_commits(paths=filename))
            commits_asc = list(reversed(commits))

            if v_from and v_to:
                idx_from = int(v_from) - 1
                idx_to = int(v_to) - 1
            else:
                idx_from = max(0, len(commits_asc) - 2)
                idx_to = len(commits_asc) - 1

            if idx_from < 0 or idx_from >= len(commits_asc) or idx_to < 0 or idx_to >= len(commits_asc):
                console.print("  [red]✗[/red]  Version out of range.")
                return

            blob_from = commits_asc[idx_from].tree / filename
            blob_to = commits_asc[idx_to].tree / filename
            text_from = blob_from.data_stream.read().decode("utf-8", errors="replace")
            text_to = blob_to.data_stream.read().decode("utf-8", errors="replace")

            import difflib
            diff_lines = list(difflib.unified_diff(
                text_from.splitlines(keepends=True),
                text_to.splitlines(keepends=True),
                fromfile=f"v{idx_from + 1}",
                tofile=f"v{idx_to + 1}",
            ))
            if diff_lines:
                diff_text = "".join(diff_lines)
                console.print(Syntax(diff_text, "diff", theme="monokai", word_wrap=True))
            else:
                console.print("  [dim]No changes between these versions.[/dim]")
        except Exception as e:
            console.print(f"  [red]✗[/red]  Could not generate diff: {e}")

    # ── rollback ──────────────────────────────────────────────────
    def rollback(self, name: str, version: int) -> None:
        """Restore a prompt to a previous version."""
        filename = self._filename(name)
        try:
            commits = list(self.repo.iter_commits(paths=filename))
            commits_asc = list(reversed(commits))
            idx = version - 1

            if idx < 0 or idx >= len(commits_asc):
                console.print("  [red]✗[/red]  Version out of range.")
                return

            blob = commits_asc[idx].tree / filename
            content = blob.data_stream.read().decode("utf-8", errors="replace")
            file_path = self.prompts_dir / filename
            file_path.write_text(content, encoding="utf-8")

            # Commit the rollback
            self.repo.index.add([filename])
            self.repo.index.commit(f"rollback: {name} to v{version}")
        except Exception as e:
            console.print(f"  [red]✗[/red]  Rollback failed: {e}")
