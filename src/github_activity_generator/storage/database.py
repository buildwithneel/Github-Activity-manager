"""SQLite local database for contribution cache, plans, and operation metadata."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from github_activity_generator.exceptions import StorageError


class ActivityDatabase:
    """Manages local SQLite persistence in ~/.github-activity-generator/activity.db."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as exc:
            raise StorageError(f"Database connection failed: {exc}") from exc

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS contribution_cache (
                    username TEXT NOT NULL,
                    contrib_date TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    weekday INTEGER NOT NULL,
                    fetched_at TEXT NOT NULL,
                    PRIMARY KEY (username, contrib_date)
                );

                CREATE TABLE IF NOT EXISTS saved_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    plan_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS operation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    details TEXT NOT NULL
                );
                """
            )

    def cache_contributions(self, username: str, contributions: dict[str, int]) -> None:
        """Upsert retrieved daily contribution counts for a GitHub user."""
        now = datetime.now(UTC).isoformat()
        rows = []
        for date_str, count in contributions.items():
            weekday = datetime.strptime(date_str, "%Y-%m-%d").weekday()
            rows.append((username, date_str, int(count), weekday, now))

        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO contribution_cache (username, contrib_date, count, weekday, fetched_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(username, contrib_date) DO UPDATE SET
                    count = excluded.count,
                    weekday = excluded.weekday,
                    fetched_at = excluded.fetched_at
                """,
                rows,
            )

    def get_cached_contributions(
        self,
        username: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, int]:
        """Retrieve cached contribution counts for a user and optional date range."""
        query = "SELECT contrib_date, count FROM contribution_cache WHERE username = ?"
        params: list[Any] = [username]
        if start_date:
            query += " AND contrib_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND contrib_date <= ?"
            params.append(end_date)
        query += " ORDER BY contrib_date ASC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return {row["contrib_date"]: int(row["count"]) for row in rows}

    def save_plan(self, name: str, config: dict[str, Any], plan: dict[str, int]) -> int:
        """Save a generated activity plan locally."""
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO saved_plans (name, created_at, config_json, plan_json)
                VALUES (?, ?, ?, ?)
                """,
                (name, now, json.dumps(config), json.dumps(plan)),
            )
            return int(cursor.lastrowid or 0)

    def list_plans(self) -> list[dict[str, Any]]:
        """List saved activity plans."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, created_at, config_json, plan_json FROM saved_plans ORDER BY id DESC"
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "created_at": row["created_at"],
                    "config": json.loads(row["config_json"]),
                    "plan": json.loads(row["plan_json"]),
                }
                for row in rows
            ]

    def record_operation(self, operation: str, details: str) -> None:
        """Record a non-sensitive audit entry for local operations."""
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO operation_history (timestamp, operation, details) VALUES (?, ?, ?)",
                (now, operation, details),
            )

    def clear_all_data(self) -> None:
        """Clear all cached contributions, saved plans, and operation history."""
        with self._connect() as conn:
            conn.executescript(
                """
                DELETE FROM contribution_cache;
                DELETE FROM saved_plans;
                DELETE FROM operation_history;
                """
            )
