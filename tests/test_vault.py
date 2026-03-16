"""Tests for PromptVault (core orchestrator)."""
from __future__ import annotations

from pathlib import Path

import pytest

from prompt_stash.config import VaultConfig
from prompt_stash.vault import PromptVault


@pytest.fixture
def vault(tmp_path: Path) -> PromptVault:
    config = VaultConfig(vault_dir=tmp_path / ".prompt_stash")
    config._ensure_dirs()
    config._ensure_git()
    return PromptVault(config)


class TestPromptVault:
    def test_save_and_get(self, vault: PromptVault) -> None:
        result = vault.save("my-prompt", content="Hello world", tags=["test"], model="claude")
        assert result["version"] == 1

        prompt = vault.get("my-prompt")
        assert prompt is not None
        assert "Hello world" in prompt["content"]
        assert prompt["model"] == "claude"

    def test_save_updates_version(self, vault: PromptVault) -> None:
        vault.save("vp", content="v1")
        result = vault.save("vp", content="v2")
        assert result["version"] == 2

    def test_get_nonexistent(self, vault: PromptVault) -> None:
        assert vault.get("nonexistent") is None

    def test_list(self, vault: PromptVault) -> None:
        vault.save("a", content="A")
        vault.save("b", content="B")
        prompts = vault.list()
        assert len(prompts) == 2

    def test_list_filter_by_tag(self, vault: PromptVault) -> None:
        vault.save("p1", content="X", tags=["python"])
        vault.save("p2", content="Y", tags=["rust"])
        results = vault.list(tag="python")
        assert len(results) == 1
        assert results[0]["name"] == "p1"

    def test_search(self, vault: PromptVault) -> None:
        vault.save("django-debug", content="Debug Django", description="Django debugger")
        vault.save("react-comp", content="React stuff")
        results = vault.search(query="django")
        assert len(results) >= 1
        assert results[0]["name"] == "django-debug"

    def test_delete(self, vault: PromptVault) -> None:
        vault.save("to-del", content="Delete me")
        vault.delete("to-del")
        assert vault.get("to-del") is None

    def test_add_tags(self, vault: PromptVault) -> None:
        vault.save("tagged", content="T", tags=["a"])
        vault.add_tags("tagged", ["b", "c"])
        prompt = vault.get("tagged")
        assert prompt is not None
        assert "b" in prompt["tags"]
        assert "c" in prompt["tags"]

    def test_export_json(self, vault: PromptVault, tmp_path: Path) -> None:
        vault.save("exp", content="Export me")
        out = tmp_path / "export.json"
        vault.export(str(out), "json")
        assert out.exists()
        import json
        data = json.loads(out.read_text())
        assert len(data) >= 1

    def test_import_json(self, vault: PromptVault, tmp_path: Path) -> None:
        import json
        src = tmp_path / "import.json"
        src.write_text(json.dumps([{"name": "imported", "content": "Hello"}]))
        count = vault.import_from(str(src))
        assert count == 1
        assert vault.get("imported") is not None
