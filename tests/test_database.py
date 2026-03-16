"""Tests for VaultDatabase."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from promptvault.database import PromptRecord, VaultDatabase


@pytest.fixture
def db(tmp_path: Path) -> VaultDatabase:
    return VaultDatabase(tmp_path / "test.db")


def _make_record(name: str = "test-prompt", **kwargs) -> PromptRecord:
    defaults = dict(
        name=name,
        description="A test prompt",
        tags=["python", "test"],
        model="claude",
        created="2025-01-01T00:00:00",
        updated="2025-01-01T00:00:00",
        uses=0,
        version=1,
        content_preview="This is a test prompt body preview",
    )
    defaults.update(kwargs)
    return PromptRecord(**defaults)


class TestVaultDatabase:
    def test_upsert_and_get(self, db: VaultDatabase) -> None:
        record = _make_record()
        db.upsert(record)
        result = db.get("test-prompt")
        assert result is not None
        assert result["name"] == "test-prompt"
        assert result["model"] == "claude"

    def test_upsert_increments_version(self, db: VaultDatabase) -> None:
        db.upsert(_make_record())
        db.upsert(_make_record(description="Updated"))
        result = db.get("test-prompt")
        assert result is not None
        assert result["version"] == 2

    def test_tags(self, db: VaultDatabase) -> None:
        db.upsert(_make_record(tags=["django", "debug"]))
        result = db.get("test-prompt")
        assert result is not None
        tag_list = result.get("tag_list", "")
        assert "django" in tag_list
        assert "debug" in tag_list

    def test_search_fts(self, db: VaultDatabase) -> None:
        db.upsert(_make_record("django-debug", description="Debug Django ORM"))
        db.upsert(_make_record("react-component", description="React component design"))
        results = db.search("django")
        assert len(results) >= 1
        assert results[0]["name"] == "django-debug"

    def test_search_by_tag(self, db: VaultDatabase) -> None:
        db.upsert(_make_record("p1", tags=["python"]))
        db.upsert(_make_record("p2", tags=["rust"]))
        results = db.search("", tag="python")
        assert len(results) == 1
        assert results[0]["name"] == "p1"

    def test_search_by_model(self, db: VaultDatabase) -> None:
        db.upsert(_make_record("p1", model="claude"))
        db.upsert(_make_record("p2", model="gpt4o"))
        results = db.search("", model="claude")
        assert len(results) == 1
        assert results[0]["name"] == "p1"

    def test_delete(self, db: VaultDatabase) -> None:
        db.upsert(_make_record())
        db.delete("test-prompt")
        assert db.get("test-prompt") is None

    def test_increment_uses(self, db: VaultDatabase) -> None:
        db.upsert(_make_record())
        db.increment_uses("test-prompt")
        db.increment_uses("test-prompt")
        result = db.get("test-prompt")
        assert result is not None
        assert result["uses"] == 2

    def test_all(self, db: VaultDatabase) -> None:
        db.upsert(_make_record("a"))
        db.upsert(_make_record("b"))
        db.upsert(_make_record("c"))
        results = db.all()
        assert len(results) == 3

    def test_rename(self, db: VaultDatabase) -> None:
        db.upsert(_make_record("old-name"))
        db.rename("old-name", "new-name")
        assert db.get("old-name") is None
        assert db.get("new-name") is not None

    def test_update_tags(self, db: VaultDatabase) -> None:
        db.upsert(_make_record(tags=["a"]))
        db.update_tags("test-prompt", ["x", "y"])
        result = db.get("test-prompt")
        tag_list = result.get("tag_list", "")
        assert "x" in tag_list
        assert "y" in tag_list
        assert "a" not in tag_list
