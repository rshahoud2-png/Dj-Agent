from __future__ import annotations

from pydantic import BaseModel, Field


class FolderRequest(BaseModel):
    folder: str


class TrackRequest(BaseModel):
    track_id: int


class TransitionRequest(BaseModel):
    current_track_id: int
    next_track_id: int
    desired_energy_direction: str | None = None


class SetRequest(BaseModel):
    event_type: str
    event_duration: int = Field(default=120, ge=30, le=720)
    name: str = Field(default="DJ Agent Set", min_length=1, max_length=120)


class ExportRequest(BaseModel):
    format: str
    destination: str


class DjSoftwareExportRequest(BaseModel):
    target: str
    destination: str
