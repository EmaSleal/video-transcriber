"""
Reclassification logic — re-check segments currently in a category against
the up-to-date category set and move whichever ones now fit better
elsewhere. Used by src/tui/tabs/video.py's "Analizar otros" flow
(session-scoped, "Otro" only).
"""

import asyncio

from src.db.database import Category
import src.db.database as db
from src.video.classifier import classify_segments_batch


def find_otro_category(categories: list[Category]) -> Category | None:
    """Locate the fallback 'Otro'/'Otros' category by name, case-insensitive.

    Pure function — no side effects, easy to test without Textual.
    """
    return next((c for c in categories if c.name.lower() in ("otro", "otros")), None)


async def reclassify_otros(session_id: int) -> int:
    """
    Re-check current 'Otro' segments of a session against the full, up-to-date
    category set (including categories just added) — without reprocessing the
    whole video. Returns the number of segments moved.
    """
    categories = db.get_categories()
    otros = find_otro_category(categories)
    if otros is None:
        return 0

    segments = db.get_segments_by_category(session_id, otros.id)
    if not segments:
        return 0

    candidates = [c for c in categories if c.id != otros.id]
    texts = [s.text for s in segments]
    loop = asyncio.get_running_loop()
    cat_ids = await loop.run_in_executor(
        None, lambda: classify_segments_batch(texts, candidates)
    )

    moved = 0
    for seg, cat_id in zip(segments, cat_ids):
        if cat_id is not None:
            db.update_segment_category(seg.id, cat_id)
            moved += 1
    return moved
