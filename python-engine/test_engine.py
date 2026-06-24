from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ["DJ_AGENT_DB_PATH"] = str(Path(tempfile.gettempdir()) / "dj-agent-desktop-test.db")

from app.database import DB_PATH, init_database, rows


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


if __name__ == "__main__":
    unittest.main()
