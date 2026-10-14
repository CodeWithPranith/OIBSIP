"""SQLite storage for BMI records (multi-user)."""

import sqlite3
from datetime import datetime
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".bmi_tracker" / "bmi_records.db"


class DatabaseError(Exception):
    """Raised for any database read/write problem, with a friendly message."""


class BMIDatabase:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = str(db_path)
        try:
            if self.db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path)
            self._create_tables()
        except (sqlite3.Error, OSError) as exc:
            raise DatabaseError(f"Could not open the database: {exc}") from exc

    def _create_tables(self):
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT NOT NULL,
                    weight_kg REAL NOT NULL,
                    height_m REAL NOT NULL,
                    bmi REAL NOT NULL,
                    category TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
                """
            )

    def save_record(self, user_name, weight_kg, height_m, bmi, category, recorded_at=None):
        """Insert one record. Returns the new row id."""
        user_name = user_name.strip()
        if not user_name:
            raise DatabaseError("A user name is required to save a record.")
        recorded_at = recorded_at or datetime.now().isoformat(timespec="seconds")
        try:
            with self._conn:
                cursor = self._conn.execute(
                    "INSERT INTO records (user_name, weight_kg, height_m, bmi, category, recorded_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (user_name, weight_kg, height_m, bmi, category, recorded_at),
                )
            return cursor.lastrowid
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not save the record: {exc}") from exc

    def get_users(self):
        """All distinct user names, alphabetically (case-insensitive)."""
        try:
            rows = self._conn.execute(
                "SELECT DISTINCT user_name FROM records ORDER BY user_name COLLATE NOCASE"
            ).fetchall()
            return [row[0] for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not read users: {exc}") from exc

    def get_history(self, user_name):
        """All records for one user, oldest first, as a list of dicts."""
        try:
            rows = self._conn.execute(
                "SELECT id, user_name, weight_kg, height_m, bmi, category, recorded_at "
                "FROM records WHERE user_name = ? COLLATE NOCASE "
                "ORDER BY recorded_at, id",
                (user_name.strip(),),
            ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not read history: {exc}") from exc
        keys = ["id", "user_name", "weight_kg", "height_m", "bmi", "category", "recorded_at"]
        return [dict(zip(keys, row)) for row in rows]

    def close(self):
        self._conn.close()
