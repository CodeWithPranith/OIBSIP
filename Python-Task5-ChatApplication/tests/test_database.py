import pytest

from web_chat.database import (
    DEFAULT_ROOM,
    ChatDatabase,
    ChatDatabaseError,
    RoomExistsError,
    UserExistsError,
)


@pytest.fixture
def db(tmp_path):
    return ChatDatabase(tmp_path / "chat.db")


def test_default_room_exists(db):
    assert DEFAULT_ROOM in db.list_rooms()


def test_create_and_get_user(db):
    db.create_user("alice", "hash123")
    assert db.get_user("alice") == {"username": "alice", "password_hash": "hash123"}
    assert db.get_user("nobody") is None


def test_duplicate_username_is_case_insensitive(db):
    db.create_user("Alice", "h")
    with pytest.raises(UserExistsError):
        db.create_user("alice", "h2")


def test_rooms(db):
    db.create_room("python")
    assert db.room_exists("python")
    assert "python" in db.list_rooms()
    with pytest.raises(RoomExistsError):
        db.create_room("python")


def test_history_order_and_limit(db):
    for i in range(7):
        db.add_message("general", "alice", f"msg{i}")
    history = db.get_history("general", limit=5)
    assert [m["text"] for m in history] == ["msg2", "msg3", "msg4", "msg5", "msg6"]


def test_history_is_per_room(db):
    db.create_room("other")
    db.add_message("general", "alice", "in general")
    db.add_message("other", "bob", "in other")
    assert [m["text"] for m in db.get_history("other")] == ["in other"]


def test_history_survives_new_database_object(tmp_path):
    path = tmp_path / "persist.db"
    ChatDatabase(path).add_message("general", "alice", "saved")
    assert ChatDatabase(path).get_history("general")[0]["text"] == "saved"


def test_sql_injection_attempts_are_inert(db):
    db.create_user("bob", "h")
    assert db.get_user("bob' OR '1'='1") is None
    db.add_message("general", "bob", "'); DROP TABLE messages; --")
    assert db.get_history("general")[0]["text"] == "'); DROP TABLE messages; --"


def test_unopenable_database_raises_friendly_error(tmp_path):
    with pytest.raises(ChatDatabaseError):
        ChatDatabase(tmp_path / "missing_folder" / "x.db")
