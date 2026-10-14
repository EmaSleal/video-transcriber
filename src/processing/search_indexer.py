"""
Semantic search indexing for video segments — a second Chroma-backed
search surface alongside the full-text SQL search
(src/db/database.py:search_segments) — this is optional, OpenAI-gated, and
degrades silently without it.
"""

import asyncio
import logging
import os

from openai import AsyncOpenAI

from src.db.database import get_segments_by_ids
from src.rag.segments_store import SegmentsSearchStore

logger = logging.getLogger("video_transcriber.processing.search_indexer")


def _build_openai_client() -> AsyncOpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    return AsyncOpenAI(api_key=api_key) if api_key else None


def index_segment(source: str, segment_id: int, text: str) -> bool:
    """Best-effort, sync entrypoint — bridges to the store's async
    interface via asyncio.run(). Safe because the only caller
    (src/video/pipeline.py) always runs inside a run_in_executor worker
    thread with no event loop of its own already running."""
    openai_client = _build_openai_client()
    store = SegmentsSearchStore(openai_client=openai_client)
    return asyncio.run(store.add_segment(source, segment_id, text))


async def _forget_segment_embeddings(source: str, segment_ids: list[int]) -> None:
    openai_client = _build_openai_client()
    store = SegmentsSearchStore(openai_client=openai_client)
    for segment_id in segment_ids:
        await store.delete_segment(source, segment_id)


def forget_segment_embeddings(source: str, segment_ids: list[int]) -> None:
    """Best-effort delete of segment embeddings — failures never block the
    SQLite soft-delete that already happened in the caller."""
    if not segment_ids:
        return
    try:
        asyncio.run(_forget_segment_embeddings(source, segment_ids))
    except Exception as e:
        logger.error("forget_segment_embeddings failed for source=%s ids=%s: %s", source, segment_ids, e)


async def search_segments_semantic(query: str, top_k: int = 5) -> list[dict]:
    """Semantic search across video segments, joined back to full SQL
    rows. A composite id the store returns but that no longer resolves to
    a real row (deleted session, etc.) is silently dropped."""
    openai_client = _build_openai_client()
    store = SegmentsSearchStore(openai_client=openai_client)
    ranked = await store.search(query, top_k=top_k)

    video_ids = [seg_id for source, seg_id, _ in ranked if source == "video"]
    video_by_id = {s.id: s for s in get_segments_by_ids(video_ids)}

    results: list[dict] = []
    for source, seg_id, _distance in ranked:
        if source == "video" and seg_id in video_by_id:
            seg = video_by_id[seg_id]
            results.append({
                "source": "video", "id": seg.id, "text": seg.text,
                "session_id": seg.session_id, "start_s": seg.start_s,
            })
    return results
