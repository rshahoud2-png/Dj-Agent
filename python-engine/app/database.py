from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


def app_data_dir() -> Path:
    base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    path = base / "DJ Agent Desktop"
    path.mkdir(parents=True, exist_ok=True)
    return path


_configured_path = os.getenv("DJ_AGENT_DB_PATH")
DB_PATH = Path(_configured_path) if _configured_path else app_data_dir() / "dj-agent.db"


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
        db.commit()
    finally:
        db.close()


def init_database() -> None:
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                title TEXT NOT NULL,
                artist TEXT NOT NULL DEFAULT '',
                album TEXT NOT NULL DEFAULT '',
                extension TEXT NOT NULL,
                file_size INTEGER NOT NULL DEFAULT 0,
                modified_at REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY,
                track_id INTEGER NOT NULL UNIQUE REFERENCES tracks(id) ON DELETE CASCADE,
                bpm REAL NOT NULL,
                duration REAL NOT NULL,
                beat_timestamps TEXT NOT NULL,
                energy_curve TEXT NOT NULL,
                intro_cue REAL NOT NULL,
                mix_in_cue REAL NOT NULL,
                drop_cue REAL NOT NULL,
                mix_out_cue REAL NOT NULL,
                loop_cue TEXT NOT NULL,
                confidence_scores TEXT NOT NULL,
                analysis_confidence REAL NOT NULL,
                warnings TEXT NOT NULL,
                analyzed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cue_points (
                id INTEGER PRIMARY KEY,
                track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
                label TEXT NOT NULL,
                name TEXT NOT NULL,
                timestamp REAL NOT NULL,
                reason TEXT NOT NULL,
                confidence REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transitions (
                id INTEGER PRIMARY KEY,
                from_track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
                to_track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
                compatibility_score INTEGER NOT NULL,
                transition_type TEXT NOT NULL,
                transition_bars INTEGER NOT NULL,
                instruction TEXT NOT NULL,
                warnings TEXT NOT NULL,
                UNIQUE(from_track_id, to_track_id)
            );

            CREATE TABLE IF NOT EXISTS setlists (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_duration INTEGER NOT NULL,
                confidence_score REAL NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_tracks_status ON tracks(status);
            CREATE INDEX IF NOT EXISTS idx_cues_track ON cue_points(track_id);
            """
        )
        db.execute("UPDATE tracks SET status='pending', error=NULL WHERE status='analyzing'")


def rows(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connection() as db:
        return [dict(row) for row in db.execute(query, params).fetchall()]


def row(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with connection() as db:
        result = db.execute(query, params).fetchone()
        return dict(result) if result else None


def json_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
