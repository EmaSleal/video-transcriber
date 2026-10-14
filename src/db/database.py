"""
Capa de acceso a datos. SQLite propia de video-transcriber.

This module owns connection lifecycle, schema DDL, migrations, seed data
and audit logging — a single cohesive responsibility. Per-table
dataclasses and CRUD DAOs live in their own modules under `src/db/`
(categories.py, video_sessions.py, segments.py) and are re-exported below
so `from src.db.database import X` keeps working for every symbol
previously defined here.

Schema:
  categories     → taxonomía editable desde la TUI
  video_sessions → una sesión de video procesada
  segments       → fragmentos de transcripción con categoría asignada
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime

from src.core.paths import app_home

DB_PATH = app_home() / "data" / "app.db"


@contextmanager
def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            color       TEXT NOT NULL DEFAULT '#6366f1'
        );

        CREATE TABLE IF NOT EXISTS video_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            url         TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'pending',
            created_at  TEXT NOT NULL,
            html_report TEXT,
            error_msg   TEXT
        );

        CREATE TABLE IF NOT EXISTS segments (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    INTEGER NOT NULL REFERENCES video_sessions(id),
            start_s       REAL NOT NULL,
            end_s         REAL NOT NULL,
            text          TEXT NOT NULL,
            category_id   INTEGER REFERENCES categories(id),
            keyframe_path TEXT
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            actor       TEXT NOT NULL,
            action      TEXT NOT NULL,
            table_name  TEXT NOT NULL,
            row_id      INTEGER NOT NULL,
            details     TEXT,
            created_at  TEXT NOT NULL
        );
        """)
        _seed_categories(conn)
        _migrate(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    """Additive, idempotent schema migrations.

    Each guard reads PRAGMA table_info once per table and only issues ALTER
    TABLE when the column is absent — safe to run on every init_db() call.
    """
    cat_cols = {r[1] for r in conn.execute("PRAGMA table_info(categories)").fetchall()}
    if "parent_id" not in cat_cols:
        conn.execute("ALTER TABLE categories ADD COLUMN parent_id INTEGER REFERENCES categories(id)")

    for table in ("categories", "video_sessions", "segments"):
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if "deleted_at" not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN deleted_at TEXT")


def _write_audit_log(
    conn: sqlite3.Connection, actor: str, action: str, table_name: str, row_id: int, details: str = ""
) -> None:
    conn.execute(
        "INSERT INTO audit_log (actor, action, table_name, row_id, details, created_at) VALUES (?,?,?,?,?,?)",
        (actor, action, table_name, row_id, details, datetime.now().isoformat()),
    )


def _seed_categories(conn: sqlite3.Connection) -> None:
    """Categorías iniciales — solo se insertan si la tabla está vacía."""
    count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if count > 0:
        return
    defaults = [
        ("Técnico", "Discusión técnica, arquitectura, código.", "#4f46e5"),
        ("Producto", "Features, roadmap, decisiones de producto.", "#059669"),
        ("Otro", "Sin categoría clara.", "#6b7280"),
    ]
    conn.executemany(
        "INSERT INTO categories (name, description, color) VALUES (?,?,?)", defaults
    )


# ── Re-exports — cada DAO module importa `from src.db import database`
# y usa `database._conn()`/`database._write_audit_log()` directamente, así
# que este bloque solo existe para que `from src.db.database import X`
# siga funcionando para cada symbol históricamente definido acá. ──

from src.db.categories import (
    Category,
    create_category,
    delete_category,
    get_categories,
    update_category,
)
from src.db.video_sessions import (
    VideoSession,
    create_video_session,
    delete_video_session,
    get_video_sessions,
    try_start_processing_session,
    update_session_status,
)
from src.db.segments import (
    Segment,
    get_segments,
    get_segments_by_category,
    get_segments_by_category_global,
    get_segments_by_ids,
    save_segment,
    search_segments,
    update_segment_category,
)
