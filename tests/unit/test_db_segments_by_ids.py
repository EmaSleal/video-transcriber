"""
Unit tests for get_segments_by_ids — bulk lookup by id, order-preserving,
needed to join semantic search results (composite "<source>:<id>" from
SegmentsSearchStore) back to full SQL rows.
"""

import pytest
from pathlib import Path


@pytest.fixture
def patched_db(tmp_path: Path, monkeypatch):
    import src.db.database as db_module
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test_segments_by_ids.db")
    db_module.init_db()
    return db_module


class TestGetSegmentsByIds:
    def test_returns_rows_preserving_caller_order(self, patched_db):
        from src.db.database import Segment

        session = patched_db.create_video_session(title="v", url="http://x")
        s1 = patched_db.save_segment(Segment(id=None, session_id=session.id, start_s=0.0, end_s=1.0, text="one"))
        s2 = patched_db.save_segment(Segment(id=None, session_id=session.id, start_s=1.0, end_s=2.0, text="two"))
        s3 = patched_db.save_segment(Segment(id=None, session_id=session.id, start_s=2.0, end_s=3.0, text="three"))

        results = patched_db.get_segments_by_ids([s3.id, s1.id])

        assert [r.id for r in results] == [s3.id, s1.id]
        assert [r.text for r in results] == ["three", "one"]

    def test_missing_ids_are_skipped_not_erroring(self, patched_db):
        from src.db.database import Segment

        session = patched_db.create_video_session(title="v", url="http://x")
        s1 = patched_db.save_segment(Segment(id=None, session_id=session.id, start_s=0.0, end_s=1.0, text="one"))

        results = patched_db.get_segments_by_ids([s1.id, 9999])

        assert [r.id for r in results] == [s1.id]

    def test_empty_ids_returns_empty_list(self, patched_db):
        assert patched_db.get_segments_by_ids([]) == []
