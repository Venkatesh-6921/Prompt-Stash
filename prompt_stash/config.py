"""
PromptVault configuration — ~/.prompt_stash/ management.

Handles first-run initialisation, config.toml reading, and path resolution.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT_VAULT_DIR = Path.home() / ".prompt_stash"
_CONFIG_TEMPLATE = """\
# PromptVault configuration
# See: https://github.com/yourname/prompt_stash

[vault]
default_model = "claude"

[github]
# repo = "https://github.com/yourname/my-prompts.git"
"""


@dataclass
class VaultConfig:
    """Resolved configuration for a PromptVault instance."""

    vault_dir: Path = field(default_factory=lambda: _DEFAULT_VAULT_DIR)
    default_model: str = "claude"
    github_repo: str = ""

    # ── derived paths ─────────────────────────────────────────────
    @property
    def prompts_dir(self) -> Path:
        return self.vault_dir / "prompts"

    @property
    def db_path(self) -> Path:
        return self.vault_dir / "vault.db"

    @property
    def config_path(self) -> Path:
        return self.vault_dir / "config.toml"

    # ── factory ───────────────────────────────────────────────────
    @classmethod
    def load(cls, vault_dir: Path | None = None) -> "VaultConfig":
        """Load (or bootstrap) configuration from *vault_dir*."""
        vdir = vault_dir or _DEFAULT_VAULT_DIR
        config = cls(vault_dir=vdir)
        config._ensure_dirs()
        config._read_toml()
        config._ensure_git()
        return config

    def save_config(self) -> None:
        """Write current configuration back to config.toml."""
        content = f"""\
# PromptVault configuration
# See: https://github.com/yourname/prompt_stash

[vault]
default_model = "{self.default_model}"

[github]
repo = "{self.github_repo}"
"""
        self.config_path.write_text(content, encoding="utf-8")

    def set_github_repo(self, url: str) -> None:
        """Update the GitHub repo URL and save to disk."""
        self.github_repo = url
        self.save_config()

    # ── private helpers ───────────────────────────────────────────
    def _ensure_dirs(self) -> None:
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def _read_toml(self) -> None:
        if not self.config_path.exists():
            self.config_path.write_text(_CONFIG_TEMPLATE, encoding="utf-8")
            return
        with open(self.config_path, "rb") as f:
            data = tomllib.load(f)
        vault_section = data.get("vault", {})
        self.default_model = vault_section.get("default_model", self.default_model)
        github_section = data.get("github", {})
        self.github_repo = github_section.get("repo", "")

    def _ensure_git(self) -> None:
        git_dir = self.prompts_dir / ".git"
        if not git_dir.exists():
            try:
                from git import Repo
                Repo.init(self.prompts_dir)
            except Exception:
                pass  # Git unavailable — degrade gracefully
