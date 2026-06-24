from __future__ import annotations

from pathlib import Path

from mutagen import File as MutagenFile

from .database import connection


SUPPORTED_SUFFIXES = {".mp3", ".wav", ".flac", ".aiff", ".aif", ".m4a", ".aac", ".ogg"}


def _first(tags: object, keys: tuple[str, ...]) -> str:
    if not tags:
        return ""
    for key in keys:
        try:
            value = tags.get(key)  # type: ignore[attr-defined]
            if value:
                if isinstance(value, list):
                    value = value[0]
                return str(value)
        except (AttributeError, KeyError, TypeError):
            continue
    return ""


def metadata(path: Path) -> tuple[str, str, str]:
    title, artist, album = path.stem, "", ""
    try:
        audio = MutagenFile(path, easy=True)
        tags = audio.tags if audio else None
        title = _first(tags, ("title", "\xa9nam")) or title
        artist = _first(tags, ("artist", "albumartist", "\xa9ART"))
        album = _first(tags, ("album", "\xa9alb"))
    except Exception:
        pass
    return title, artist, album


def scan_folder(folder: str) -> dict[str, int]:
    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Selected music folder does not exist or is not accessible.")
    discovered = added = updated = 0
    with connection() as db:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            discovered += 1
            stat = path.stat()
            existing = db.execute("SELECT id, file_size, modified_at FROM tracks WHERE path=?", (str(path),)).fetchone()
            if existing and existing["file_size"] == stat.st_size and existing["modified_at"] == stat.st_mtime:
                continue
            title, artist, album = metadata(path)
            if existing:
                db.execute(
                    """UPDATE tracks SET filename=?, title=?, artist=?, album=?, extension=?,
                       file_size=?, modified_at=?, status='pending', error=NULL, updated_at=CURRENT_TIMESTAMP
                       WHERE id=?""",
                    (path.name, title, artist, album, path.suffix.lower(), stat.st_size, stat.st_mtime, existing["id"]),
                )
                db.execute("DELETE FROM analyses WHERE track_id=?", (existing["id"],))
                db.execute("DELETE FROM cue_points WHERE track_id=?", (existing["id"],))
                updated += 1
            else:
                db.execute(
                    """INSERT INTO tracks(path, filename, title, artist, album, extension, file_size, modified_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (str(path), path.name, title, artist, album, path.suffix.lower(), stat.st_size, stat.st_mtime),
                )
                added += 1
        db.execute(
            """INSERT INTO settings(key, value) VALUES ('music_folder', ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP""",
            (str(root),),
        )
    return {"discovered": discovered, "added": added, "updated": updated}
