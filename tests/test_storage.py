"""Tests for local storage, configuration, keyring security, and SQLite database."""

import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from github_activity_generator.config import AppPaths, AppSettings, GenerationConfig
from github_activity_generator.storage.config_store import ConfigStore
from github_activity_generator.storage.database import ActivityDatabase
from github_activity_generator.storage.keyring_store import KeyringStore


class TestStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.paths = AppPaths(root=self.root)
        self.paths.ensure_dirs()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_config_store_roundtrip_and_no_secrets(self) -> None:
        store = ConfigStore(self.paths)
        settings = AppSettings(theme="light", timezone="America/New_York")
        store.save(settings)

        loaded = store.load()
        self.assertEqual(loaded.theme, "light")
        self.assertEqual(loaded.timezone, "America/New_York")

        # Ensure forbidden secret keys are stripped
        stripped = ConfigStore._strip_secrets({"theme": "dark", "access_token": "ghp_secret123"})
        self.assertNotIn("access_token", stripped)
        self.assertEqual(stripped["theme"], "dark")

    def test_export_import_generation_config(self) -> None:
        store = ConfigStore(self.paths)
        gen_cfg = GenerationConfig(
            start_date="2025-01-01",
            end_date="2025-12-31",
            min_commits_per_day=2,
            max_commits_per_day=6,
            exclude_weekends=True,
            pattern="weekday_focused",
        )
        export_path = self.paths.exports_dir / "gen_config.json"
        store.export_generation_config(gen_cfg, export_path)
        imported = store.import_generation_config(export_path)
        self.assertEqual(imported.start_date, "2025-01-01")
        self.assertEqual(imported.max_commits_per_day, 6)
        self.assertTrue(imported.exclude_weekends)

    def test_keyring_fallback_security_and_permissions(self) -> None:
        cred_file = self.paths.credentials_file
        store = KeyringStore(fallback_file=cred_file, service_name="test-gag")
        # Force fallback path for deterministic test
        store._keyring = None

        secret = "ghp_ExampleToken1234567890"
        store.set_secret("token", secret)
        self.assertEqual(store.get_secret("token"), secret)

        # File must not contain plaintext token
        raw_content = cred_file.read_text(encoding="utf-8")
        self.assertNotIn(secret, raw_content)

        # Permissions must be 0600 on POSIX
        if os.name == "posix":
            mode = stat.S_IMODE(cred_file.stat().st_mode)
            self.assertEqual(mode, 0o600)

        store.delete_secret("token")
        self.assertIsNone(store.get_secret("token"))

    def test_database_cache_plans_and_clear(self) -> None:
        db = ActivityDatabase(self.paths.db_file)
        db.cache_contributions("octocat", {"2025-01-01": 3, "2025-01-02": 0})
        cached = db.get_cached_contributions("octocat")
        self.assertEqual(cached, {"2025-01-01": 3, "2025-01-02": 0})

        plan_id = db.save_plan("test-plan", {"pattern": "consistent"}, {"2025-01-02": 2})
        self.assertGreater(plan_id, 0)
        plans = db.list_plans()
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0]["name"], "test-plan")

        db.clear_all_data()
        self.assertEqual(db.get_cached_contributions("octocat"), {})
        self.assertEqual(db.list_plans(), [])


if __name__ == "__main__":
    unittest.main()
