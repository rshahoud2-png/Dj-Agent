from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .database import DB_PATH, app_data_dir, connection


def configure_bundled_ffmpeg() -> str:
    import imageio_ffmpeg

    executable = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
    if not executable.is_file():
        raise FileNotFoundError(f"Bundled FFmpeg executable was not found at {executable}")
    os.environ["DJ_AGENT_FFMPEG_PATH"] = str(executable)
    path_values = [value for key, value in os.environ.items() if key.lower() == "path"]
    for key in [key for key in os.environ if key.lower() == "path"]:
        try:
            del os.environ[key]
        except KeyError:
            pass
    os.environ["Path"] = f"{executable.parent}{os.pathsep}{os.pathsep.join(path_values)}"
    return str(executable)


def check_writable_folder(path: Path) -> tuple[bool, str]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(prefix="dj-agent-write-", suffix=".tmp", dir=path)
        os.close(handle)
        Path(temporary).unlink(missing_ok=True)
        return True, str(path)
    except Exception as exc:
        return False, f"{path}: {exc}"


def runtime_diagnostics() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(key: str, label: str, ok: bool, details: str, repair: str = "") -> None:
        checks.append({"key": key, "label": label, "ok": ok, "details": details, "repair": repair})

    try:
        ffmpeg = configure_bundled_ffmpeg()
        version = subprocess.run(
            [ffmpeg, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).stdout.splitlines()[0]
        add("ffmpeg", "Bundled FFmpeg", True, f"{version} ({ffmpeg})")
    except Exception as exc:
        add("ffmpeg", "Bundled FFmpeg", False, str(exc), "Reinstall DJ Agent Desktop from the latest official release.")

    app_folder = app_data_dir()
    writable, details = check_writable_folder(app_folder)
    add("app_data", "App data folder writable", writable, details, "Allow write access to %LOCALAPPDATA%\\DJ Agent Desktop.")

    try:
        with connection() as db:
            db.execute("CREATE TABLE IF NOT EXISTS runtime_diagnostics (checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            db.execute("INSERT INTO runtime_diagnostics DEFAULT VALUES")
            db.execute("DELETE FROM runtime_diagnostics")
            sqlite_version = db.execute("SELECT sqlite_version()").fetchone()[0]
        add("database", "SQLite database writable", True, f"SQLite {sqlite_version} at {DB_PATH}")
    except Exception as exc:
        add("database", "SQLite database writable", False, str(exc), "Check free disk space and write access to the app data folder.")

    dependencies = (
        ("numpy", "NumPy native runtime"),
        ("scipy", "SciPy native runtime"),
        ("soundfile", "SoundFile/libsndfile runtime"),
        ("librosa", "librosa audio engine"),
    )
    for module_name, label in dependencies:
        try:
            module = __import__(module_name)
            version = getattr(module, "__version__", "included")
            if module_name == "soundfile":
                import soundfile

                soundfile.available_formats()
            add(module_name, label, True, str(version))
        except Exception as exc:
            add(module_name, label, False, str(exc), "Reinstall DJ Agent Desktop; this native dependency should be bundled.")

    add(
        "python",
        "Embedded Python runtime",
        bool(getattr(sys, "frozen", False)),
        "Packaged PyInstaller runtime" if getattr(sys, "frozen", False) else sys.executable,
        "Use the installed DJ Agent Desktop application instead of running the development script.",
    )
    return {"status": "ok" if all(item["ok"] for item in checks) else "error", "checks": checks}
