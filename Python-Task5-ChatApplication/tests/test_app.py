import pytest

from web_chat.app import clean_room_name, create_app


@pytest.fixture
def setup(tmp_path):
    app, socketio = create_app(db_path=tmp_path / "web.db", secret_key="test-key")
    app.config["TESTING"] = True
    return app, socketio


@pytest.fixture
def app(setup):
    return setup[0]


def register(client, username="alice", password="password1", confirm=None):
    return client.post("/register", data={"username": username, "password": password,
                                           "confirm": password if confirm is None else confirm})


def socket_client(setup, username):
    """A logged-in HTTP client plus a Socket.IO test client sharing its session."""
    app, socketio = setup
    http = app.test_client()
    register(http, username)
    return http, socketio.test_client(app, flask_test_client=http)


def events(client, name):
    """Payloads of received events called `name`.

    Flask-SocketIO's test client hands events named "message" back as the bare
    payload, and all other events as a list of arguments.
    """
    return [e["args"] if isinstance(e["args"], dict) else e["args"][0]
            for e in client.get_received() if e["name"] == name]


# ------------------------------------------------------------------ HTTP
def test_index_redirects_to_login(app):
    response = app.test_client().get("/")
    assert response.status_code == 302 and "/login" in response.location


def test_chat_page_requires_login(app):
    response = app.test_client().get("/chat")
    assert response.status_code == 302 and "/login" in response.location


def test_register_logs_in_and_opens_chat(app):
    client = app.test_client()
    response = register(client)
    assert response.status_code == 302 and "/chat" in response.location
    assert b"alice" in client.get("/chat").data


def test_password_is_stored_hashed(app):
    register(app.test_client())
    stored = app.db.get_user("alice")["password_hash"]
    assert "password1" not in stored and stored.startswith("pbkdf2:")


@pytest.mark.parametrize("username, password, confirm, message", [
    ("ab", "password1", None, b"Username must be"),
    ("bad name!", "password1", None, b"Username must be"),
    ("alice", "short", None, b"at least 8"),
    ("alice", "password1", "different1", b"do not match"),
])
def test_registration_validation(app, username, password, confirm, message):
    response = register(app.test_client(), username, password, confirm)
    assert response.status_code == 200 and message in response.data
    assert app.db.get_user(username) is None


def test_duplicate_registration_rejected(app):
    register(app.test_client())
    response = register(app.test_client(), "ALICE")
    assert b"already taken" in response.data


def test_login_success_and_logout(app):
    register(app.test_client())
    client = app.test_client()
    response = client.post("/login", data={"username": "alice", "password": "password1"})
    assert response.status_code == 302 and "/chat" in response.location
    assert client.get("/chat").status_code == 200
    client.post("/logout")
    assert client.get("/chat").status_code == 302


def test_login_errors_are_generic(app):
    register(app.test_client())
    wrong_password = app.test_client().post("/login", data={"username": "alice", "password": "nope"})
    wrong_user = app.test_client().post("/login", data={"username": "ghost", "password": "password1"})
    assert b"Invalid username or password" in wrong_password.data
    assert b"Invalid username or password" in wrong_user.data


def test_rooms_api_requires_login(app):
    assert app.test_client().get("/api/rooms").status_code == 401
    client = app.test_client()
    register(client)
    assert "general" in client.get("/api/rooms").get_json()["rooms"]


@pytest.mark.parametrize("raw, expected", [("My Room", "my-room"), ("python", "python"), ("a", None),
                                            ("bad!name", None), ("", None), (None, None), ("x" * 31, None)])
def test_clean_room_name(raw, expected):
    assert clean_room_name(raw) == expected


# -------------------------------------------------------------- Socket.IO
def test_anonymous_socket_connection_is_rejected(setup):
    app, socketio = setup
    assert not socketio.test_client(app).is_connected()


def test_logged_in_socket_gets_room_list(setup):
    _http, sio = socket_client(setup, "alice")
    assert sio.is_connected()
    assert "general" in events(sio, "rooms")[0]["rooms"]


def test_message_reaches_everyone_in_room_with_emoji(setup):
    _h1, alice = socket_client(setup, "alice")
    _h2, bob = socket_client(setup, "bob")
    alice.emit("join", {"room": "general"})
    bob.emit("join", {"room": "general"})
    alice.get_received(); bob.get_received()
    alice.emit("message", {"text": "hello :smile:"})
    for client in (alice, bob):
        message = events(client, "message")[0]
        assert message["username"] == "alice" and message["text"] == "hello 😄"
        assert len(message["time"]) == 5 and message["time"][2] == ":"


def test_rooms_are_isolated(setup):
    _h1, alice = socket_client(setup, "alice")
    _h2, bob = socket_client(setup, "bob")
    alice.emit("create_room", {"name": "private"})
    alice.emit("join", {"room": "private"})
    bob.emit("join", {"room": "general"})
    alice.get_received(); bob.get_received()
    alice.emit("message", {"text": "secret"})
    assert events(alice, "message") and not events(bob, "message")


def test_history_loaded_on_join_and_survives_reconnect(setup):
    _h1, alice = socket_client(setup, "alice")
    alice.emit("join", {"room": "general"})
    alice.emit("message", {"text": "first :fire:"})
    alice.emit("message", {"text": "second"})
    alice.disconnect()
    _h2, bob = socket_client(setup, "bob")
    bob.get_received()
    bob.emit("join", {"room": "general"})
    history = events(bob, "history")[0]
    assert history["room"] == "general"
    assert [m["text"] for m in history["messages"]] == ["first 🔥", "second"]
    assert history["messages"][0]["username"] == "alice"


def test_create_room_broadcasts_to_all_and_rejects_duplicates(setup):
    _h1, alice = socket_client(setup, "alice")
    _h2, bob = socket_client(setup, "bob")
    alice.get_received(); bob.get_received()
    alice.emit("create_room", {"name": "Study Group"})
    assert events(alice, "room_created")[0]["room"] == "study-group"
    assert "study-group" in events(bob, "rooms")[0]["rooms"]
    alice.emit("create_room", {"name": "study group"})
    assert "already exists" in events(alice, "error_message")[0]["error"]
    alice.emit("create_room", {"name": "!"})
    assert "Room names" in events(alice, "error_message")[0]["error"]


def test_join_unknown_room_errors(setup):
    _h, alice = socket_client(setup, "alice")
    alice.get_received()
    alice.emit("join", {"room": "nope"})
    assert "does not exist" in events(alice, "error_message")[0]["error"]


def test_message_before_joining_is_rejected(setup):
    _h, alice = socket_client(setup, "alice")
    alice.get_received()
    alice.emit("message", {"text": "hi"})
    assert "Join a room first" in events(alice, "error_message")[0]["error"]


def test_empty_overlong_and_malformed_messages(setup):
    app = setup[0]
    _h, alice = socket_client(setup, "alice")
    alice.emit("join", {"room": "general"})
    alice.get_received()
    alice.emit("message", {"text": "   "})
    alice.emit("message", "not a dict")
    alice.emit("message", {"text": 12345})
    assert not events(alice, "message")
    alice.emit("message", {"text": "x" * 501})
    assert "at most 500" in events(alice, "error_message")[0]["error"]
    assert app.db.get_history("general") == []  # nothing invalid was stored


def test_html_is_stored_and_sent_as_plain_text(setup):
    _h, alice = socket_client(setup, "alice")
    alice.emit("join", {"room": "general"})
    alice.get_received()
    alice.emit("message", {"text": "<script>alert(1)</script>"})
    # The server passes it through untouched; the browser code uses textContent.
    assert events(alice, "message")[0]["text"] == "<script>alert(1)</script>"


def test_leave_and_disconnect_notices(setup):
    _h1, alice = socket_client(setup, "alice")
    _h2, bob = socket_client(setup, "bob")
    alice.emit("join", {"room": "general"})
    bob.emit("join", {"room": "general"})
    alice.get_received(); bob.get_received()
    bob.disconnect()
    assert any("bob disconnected" in e["text"] for e in events(alice, "system"))
