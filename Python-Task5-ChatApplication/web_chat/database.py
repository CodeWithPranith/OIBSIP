"""SQLite storage for users, rooms and messages.

Every call opens its own short-lived connection, which keeps the code safe
when several Socket.IO threads use the database at the same time.
All SQL uses ? placeholders (parameterised queries) to prevent SQL injection.
"""

import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "chat.db"
DEFAULT_ROOM = "general"

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")
ROOM_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,29}$")


class ChatDatabaseError(Exception):
    """Any database problem."""


class UserExistsError(ChatDatabaseError):
    pass


class RoomExistsError(ChatDatabaseError):
    pass


class ChatDatabase:
    def __init__(self, path=DEFAULT_DB_PATH):
        self.path = str(path)
        self._create_tables()

    @contextmanager
    def _connection(self):
        try:
            connection = sqlite3.connect(self.path, timeout=10)
            connection.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            raise ChatDatabaseError(f"Cannot open database: {exc}") from exc
        try:
            with connection:  # commits on success, rolls back on error
                yield connection
        except sqlite3.IntegrityError:
            raise
        except sqlite3.Error as exc:
            raise ChatDatabaseError(f"Database error: {exc}") from exc
        finally:
            connection.close()

    def _create_tables(self):
        with self._connection() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room TEXT NOT NULL,
                    username TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_messages_room ON messages (room, id);
                """
            )
            db.execute(
                "INSERT OR IGNORE INTO rooms (name, created_at) VALUES (?, ?)",
                (DEFAULT_ROOM, _now()),
            )

    # ----- users -----
    def create_user(self, username, password_hash):
        try:
            with self._connection() as db:
                db.execute(
                    "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                    (username, password_hash, _now()),
                )
        except sqlite3.IntegrityError:
            raise UserExistsError(username) from None

    def get_user(self, username):
        with self._connection() as db:
            row = db.execute(
                "SELECT username, password_hash FROM users WHERE username = ?", (username,)
            ).fetchone()
        return dict(row) if row else None

    # ----- rooms -----
    def create_room(self, name):
        try:
            with self._connection() as db:
                db.execute("INSERT INTO rooms (name, created_at) VALUES (?, ?)", (name, _now()))
        except sqlite3.IntegrityError:
            raise RoomExistsError(name) from None

    def room_exists(self, name):
        with self._connection() as db:
            return db.execute("SELECT 1 FROM rooms WHERE name = ?", (name,)).fetchone() is not None

    def list_rooms(self):
        with self._connection() as db:
            return [row["name"] for row in db.execute("SELECT name FROM rooms ORDER BY name")]

    # ----- messages -----
    def add_message(self, room, username, text):
        with self._connection() as db:
            db.execute(
                "INSERT INTO messages (room, username, text, created_at) VALUES (?, ?, ?, ?)",
                (room, username, text, _now()),
            )

    def get_history(self, room, limit=50):
        """The last `limit` messages of a room, oldest first."""
        with self._connection() as db:
            rows = db.execute(
                "SELECT username, text, created_at FROM messages WHERE room = ? "
                "ORDER BY id DESC LIMIT ?",
                (room, limit),
            ).fetchall()
        return [
            {"username": r["username"], "text": r["text"], "time": r["created_at"][11:16]}
            for r in reversed(rows)
        ]


def _now():
    return datetime.now().isoformat(timespec="seconds")
