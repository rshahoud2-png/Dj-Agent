from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ["DJ_AGENT_DB_PATH"] = str(Path(tempfile.gettempdir()) / "dj-agent-desktop-test.db")

from app.database import DB_PATH, init_database, rows
from app.integrations import ADAPTERS, export_for_dj_software


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if DB_PATH.exists():
            DB_PATH.unlink()
        init_database()

    def test_schema_contains_required_tables(self) -> None:
        names = {item["name"] for item in rows("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"tracks", "analyses", "cue_points", "transitions", "setlists", "settings"}.issubset(names))

    def test_wal_mode_is_enabled(self) -> None:
        result = rows("PRAGMA journal_mode")
        self.assertEqual(result[0]["journal_mode"].lower(), "wal")

    def test_dj_software_adapters_write_expected_files(self) -> None:
        payload = {
            "name": "Test Set",
            "items": [
                {
                    "track": {
                        "track_id": 1,
                        "path": str(Path(tempfile.gettempdir()) / "track.mp3"),
                        "title": "Test Track",
                        "artist": "DJ Agent",
                        "estimated_bpm": 124,
                        "duration": 180,
                        "hot_cues": [
                            {"label": "Hot Cue A", "name": "Intro", "timestamp": 0},
                            {"label": "Hot Cue B", "name": "Mix In", "timestamp": 16},
                        ],
                        "loop_cue": {"start": 32, "bars": 8},
                    }
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rekordbox = export_for_dj_software(payload, "rekordbox", str(root / "rekordbox"))
            virtualdj = export_for_dj_software(payload, "virtualdj", str(root / "database"))
            serato = export_for_dj_software(payload, "serato", str(root / "crate"))
            self.assertEqual(set(ADAPTERS), {"rekordbox", "virtualdj", "serato"})
            self.assertTrue(all(Path(path).exists() for path in rekordbox + virtualdj + serato))
            self.assertEqual(len(serato), 2)


if __name__ == "__main__":
    unittest.main()
