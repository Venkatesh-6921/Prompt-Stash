"""Tests for PromptStorage."""
from __future__ import annotations

from pathlib import Path

import pytest

from prompt_stash.storage import PromptStorage


@pytest.fixture
def storage(tmp_path: Path) -> PromptStorage:
    return PromptStorage(tmp_path / "prompts")


class TestPromptStorage:
    def test_write_and_read(self, storage: PromptStorage) -> None:
        meta = {"description": "Test", "tags": ["a"], "model": "claude", "version": 1, "uses": 0}
        storage.write("test-prompt", "Hello world", meta)
        content = storage.read_content("test-prompt")
        assert content is not None
        assert "Hello world" in content

    def test_read_metadata(self, storage: PromptStorage) -> None:
        meta = {"description": "Desc", "tags": ["x", "y"], "model": "gpt4o", "version": 2, "uses": 5}
        storage.write("meta-test", "Body", meta)
        result = storage.read_metadata("meta-test")
        assert result is not None
        assert result["description"] == "Desc"
        assert result["model"] == "gpt4o"
        assert "x" in result.get("tags", [])

    def test_delete(self, storage: PromptStorage) -> None:
        storage.write("to-delete", "Content", {"description": "", "tags": [], "model": "", "version": 1, "uses": 0})
        assert storage.exists("to-delete")
        storage.delete("to-delete")
        assert not storage.exists("to-delete")

    def test_read_nonexistent(self, storage: PromptStorage) -> None:
        assert storage.read_content("nonexistent") is None
        assert storage.read_metadata("nonexistent") is None

    def test_frontmatter_roundtrip(self, storage: PromptStorage) -> None:
        body = "Line one\nLine two\nLine three"
        meta = {"description": "RT", "tags": ["round", "trip"], "model": "claude", "version": 1, "uses": 0}
        storage.write("roundtrip", body, meta)
        content = storage.read_content("roundtrip")
        assert content is not None
        assert "Line one" in content
        assert "Line three" in content
        fm = storage.read_metadata("roundtrip")
        assert fm["name"] == "roundtrip"

    def test_rename(self, storage: PromptStorage) -> None:
        storage.write("old-name", "Content", {"description": "", "tags": [], "model": "", "version": 1, "uses": 0})
        storage.rename("old-name", "new-name")
        assert not storage.exists("old-name")
        assert storage.exists("new-name")
