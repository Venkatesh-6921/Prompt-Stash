"""
GitHub push/pull sync via GitPython.
"""
from __future__ import annotations

from typing import Any

from rich.console import Console

console = Console()


class VaultSync:
    """Push / pull the prompts repo to a GitHub remote."""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.prompts_dir = config.prompts_dir
        self.github_repo = config.github_repo
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            from git import Repo
            self._repo = Repo(self.prompts_dir)
        return self._repo

    # ── push ──────────────────────────────────────────────────────
    def push(self) -> bool:
        """Push local commits to the configured GitHub remote."""
        try:
            self._ensure_remote()
            origin = self.repo.remote("origin")
            
            # origin.push() returns a list of PushInfo objects. 
            # We must inspect them to see if the push actually succeeded.
            push_results = origin.push(refspec="main:main", set_upstream=True)
            
            for info in push_results:
                # Flags like Error, Rejected, RemoteRejected indicate failure
                # 1024 is the bit for 'ERROR' in GitPython PushInfo flags
                if info.flags & info.ERROR or info.flags & info.REJECTED or info.flags & info.REMOTE_REJECTED:
                    console.print(f"  [red]✗[/red]  Push failed for {info.remote_ref_string}: {info.summary}")
                    return False
            
            return True
        except Exception as e:
            err_msg = str(e)
            if "does not appear to be a git repository" in err_msg or "Could not read from remote" in err_msg:
                console.print(f"  [red]✗[/red]  [bold]Invalid Repository URL:[/bold] '{self.github_repo}'")
                console.print("      Please ensure the URL is a genuine GitHub Git URL (ending in .git).")
            else:
                console.print(f"  [red]✗[/red]  Internal Error during push: {e}")
            return False

    # ── pull ──────────────────────────────────────────────────────
    def pull(self, source: str | None = None) -> bool:
        """Pull from the configured GitHub remote (or a custom source)."""
        try:
            url = source or self.github_repo
            if not url:
                console.print("  [yellow]⚠[/yellow]  No remote configured.")
                return False
            self._ensure_remote(url)
            origin = self.repo.remote("origin")
            
            # Use explicit branch 'main' and allow unrelated histories
            # This is often needed for the first pull if the remote has a README/License
            origin.pull(refspec="main", rebase=True, allow_unrelated_histories=True)
            return True
        except Exception as e:
            console.print(f"  [red]✗[/red]  Pull failed: {e}")
            return False

    # ── internal ──────────────────────────────────────────────────
    def _ensure_remote(self, url: str | None = None) -> None:
        target = url or self.github_repo
        if not target:
            return
        try:
            origin = self.repo.remote("origin")
            if origin.url != target:
                self.repo.delete_remote("origin")
                self.repo.create_remote("origin", target)
        except ValueError:
            self.repo.create_remote("origin", target)
