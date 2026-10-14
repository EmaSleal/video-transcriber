"""
Unit tests for global (cross-session) category lookups — used by the
"reclassify this category everywhere" pattern (mirrors Video's
session-scoped reclassify_otros, but global and works for any category,
not just "Otro"/"Otros").
"""

import pytest
from pathlib import Path


@pytest.fixture
def patched_db(tmp_path: Path, monkeypatch):
    import src.db.database as db_module
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test_category_global.db")
    db_module.init_db()
    return db_module


class TestGetSegmentsByCategoryGlobal:
    def test_returns_matches_across_multiple_sessions(self, patched_db):
        from src.db.database import Segment

        cat = patched_db.create_category("Categoría Test", "desc")
        s1 = patched_db.create_video_session(title="v1", url="http://x")
        s2 = patched_db.create_video_session(title="v2", url="http://y")
        seg1 = patched_db.save_segment(
            Segment(id=None, session_id=s1.id, start_s=0.0, end_s=1.0, text="uno", category_id=cat.id)
        )
        seg2 = patched_db.save_segment(
            Segment(id=None, session_id=s2.id, start_s=0.0, end_s=1.0, text="dos", category_id=cat.id)
        )
        patched_db.save_segment(
            Segment(id=None, session_id=s1.id, start_s=1.0, end_s=2.0, text="otro", category_id=None)
        )

        results = patched_db.get_segments_by_category_global(cat.id)

        assert {r.id for r in results} == {seg1.id, seg2.id}

    def test_no_matches_returns_empty_list(self, patched_db):
        cat = patched_db.create_category("Categoría Test", "desc")
        assert patched_db.get_segments_by_category_global(cat.id) == []


class TestDeleteCategory:
    def test_deleting_parent_category_promotes_children_to_top_level(self, patched_db):
        """Children keep existing, never cascade-deleted, with parent_id
        reset to NULL."""
        parent = patched_db.create_category("Diseño UI/UX", "desc padre")
        child = patched_db.create_category("Tipografía", "desc hijo", parent_id=parent.id)

        patched_db.delete_category(parent.id)

        remaining = {c.id: c for c in patched_db.get_categories()}
        assert child.id in remaining
        assert remaining[child.id].parent_id is None
