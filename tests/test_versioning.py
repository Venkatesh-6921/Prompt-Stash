"""Tests for PromptVersioning."""
from __future__ import annotations

from pathlib import Path

import pytest
from git import Repo

from promptvault.config import VaultConfig
from promptvault.versioning import PromptVersioning


@pytest.fixture
def versioning_env(tmp_path: Path):
    """Set up a temp vault with Git and some commits."""
    vault_dir = tmp_path / ".promptvault"
    prompts_dir = vault_dir / "prompts"
    prompts_dir.mkdir(parents=True)
    repo = Repo.init(prompts_dir)

    # Write v1
    f = prompts_dir / "my-prompt.md"
    f.write_text("---\nname: my-prompt\n---\n\nVersion one")
    repo.index.add(["my-prompt.md"])
    repo.index.commit("add: my-prompt")

    # Write v2
    f.write_text("---\nname: my-prompt\n---\n\nVersion two")
    repo.index.add(["my-prompt.md"])
    repo.index.commit("update: my-prompt")

    # Write v3
    f.write_text("---\nname: my-prompt\n---\n\nVersion three")
    repo.index.add(["my-prompt.md"])
    repo.index.commit("update: my-prompt")

    config = VaultConfig(vault_dir=vault_dir)
    return PromptVersioning(config), prompts_dir


class TestPromptVersioning:
    def test_log_returns_entries(self, versioning_env) -> None:
        v, _ = versioning_env
        entries = v.log("my-prompt")
        assert len(entries) == 3
        assert entries[0]["version"] == 1
        assert entries[2]["version"] == 3

    def test_log_empty_for_unknown(self, versioning_env) -> None:
        v, _ = versioning_env
        assert v.log("nonexistent") == []

    def test_rollback(self, versioning_env) -> None:
        v, prompts_dir = versioning_env
        v.rollback("my-prompt", 1)
        content = (prompts_dir / "my-prompt.md").read_text()
        assert "Version one" in content

    def test_rollback_creates_commit(self, versioning_env) -> None:
        v, _ = versioning_env
        v.rollback("my-prompt", 2)
        entries = v.log("my-prompt")
        assert len(entries) == 4  # 3 original + 1 rollback
        assert "rollback" in entries[3]["message"]
