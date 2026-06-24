from __future__ import annotations

import asyncio
import gc
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .analysis import MAX_ANALYSIS_SECONDS, SAMPLE_RATE, cue_points
from .database import DB_PATH, connection, init_database
from .models import ExportRequest, FolderRequest, SetRequest, TrackRequest, TransitionRequest
from .scanner import SUPPORTED_SUFFIXES, scan_folder
from .service import analyze_track, export_setlist, generate_setlist, get_analysis, list_tracks, transition


analysis_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield


app = FastAPI(title="DJ Agent Desktop Engine", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:1420", "http://localhost:1420", "tauri://localhost", "http://tauri.localhost", "https://tauri.localhost"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["content-type"],
)


def bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "dj-agent-desktop-engine",
        "sample_rate": SAMPLE_RATE,
        "max_analysis_seconds": MAX_ANALYSIS_SECONDS,
        "supported_suffixes": sorted(SUPPORTED_SUFFIXES),
        "database_path": str(DB_PATH),
    }


@app.post("/scan-library")
def scan_library(request: FolderRequest) -> dict[str, int]:
    try:
        return scan_folder(request.folder)
    except Exception as exc:
        raise bad_request(exc) from exc


@app.get("/tracks")
def tracks() -> list[dict[str, Any]]:
    return list_tracks()


@app.get("/tracks/{track_id}/analysis")
def track_analysis(track_id: int) -> dict[str, Any]:
    try:
        return get_analysis(track_id)
    except Exception as exc:
        raise bad_request(exc) from exc


@app.post("/analyze-track")
async def analyze(request: TrackRequest) -> dict[str, Any]:
    try:
        async with analysis_lock:
            return await asyncio.to_thread(analyze_track, request.track_id)
    except Exception as exc:
        raise bad_request(exc) from exc
    finally:
        gc.collect()


@app.post("/generate-cues")
def generate_cues(request: TrackRequest) -> dict[str, Any]:
    try:
        analysis = get_analysis(request.track_id)
        cues = cue_points(analysis)
        with connection() as db:
            db.execute("DELETE FROM cue_points WHERE track_id=?", (request.track_id,))
            db.executemany(
                "INSERT INTO cue_points(track_id, label, name, timestamp, reason, confidence) VALUES (?, ?, ?, ?, ?, ?)",
                [(request.track_id, cue["label"], cue["name"], cue["timestamp"], cue["reason"], cue["confidence"]) for cue in cues],
            )
        return get_analysis(request.track_id)
    except Exception as exc:
        raise bad_request(exc) from exc


@app.post("/analyze-transition")
def analyze_transition(request: TransitionRequest) -> dict[str, Any]:
    try:
        return transition(get_analysis(request.current_track_id), get_analysis(request.next_track_id))
    except Exception as exc:
        raise bad_request(exc) from exc


@app.post("/generate-set-analysis")
def generate_set_analysis(request: SetRequest) -> dict[str, Any]:
    try:
        return generate_setlist(request.event_type, request.event_duration, request.name)
    except Exception as exc:
        raise bad_request(exc) from exc


@app.post("/setlists/{setlist_id}/export")
def export(setlist_id: int, request: ExportRequest) -> dict[str, str]:
    try:
        return {"path": export_setlist(setlist_id, request.format, request.destination)}
    except Exception as exc:
        raise bad_request(exc) from exc
