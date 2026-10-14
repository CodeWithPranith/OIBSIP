"""Flask + Socket.IO web chat: accounts, rooms, history, emoji."""

import os
import secrets
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import check_password_hash, generate_password_hash

from .database import (
    DEFAULT_ROOM,
    ROOM_PATTERN,
    USERNAME_PATTERN,
    ChatDatabase,
    ChatDatabaseError,
    RoomExistsError,
    UserExistsError,
)
from .emoji_map import replace_shortcodes

MAX_MESSAGE_LENGTH = 500
MIN_PASSWORD_LENGTH = 8
# pbkdf2 is available in every Python build, including the macOS system Python.
PASSWORD_HASH_METHOD = "pbkdf2:sha256"


def _clock():
    return datetime.now().strftime("%H:%M")


def clean_room_name(raw):
    """Normalise a room name ('My Room' -> 'my-room'); None if it is invalid."""
    if not isinstance(raw, str):
        return None
    name = raw.strip().lower().replace(" ", "-")
    return name if ROOM_PATTERN.match(name) else None


def create_app(db_path=None, secret_key=None):
    """Build the Flask app. Returns (app, socketio)."""
    app = Flask(__name__)
    # Without CHAT_SECRET_KEY a random key is used: it works, but every restart
    # logs everybody out because the old session cookies stop being valid.
    app.config["SECRET_KEY"] = secret_key or os.environ.get("CHAT_SECRET_KEY") or secrets.token_hex(32)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    db = ChatDatabase(db_path) if db_path else ChatDatabase()
    app.db = db
    # No cors_allowed_origins set -> only pages served by this app may connect.
    socketio = SocketIO(app, async_mode="threading")
    room_of_session = {}  # Socket.IO session id -> room the user is currently in

    # ------------------------------------------------------------ HTTP pages
    @app.route("/")
    def index():
        return redirect(url_for("chat" if "username" in session else "login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        error = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm", "")
            if not USERNAME_PATTERN.match(username):
                error = "Username must be 3-20 characters: letters, numbers or underscore."
            elif len(password) < MIN_PASSWORD_LENGTH:
                error = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            elif password != confirm:
                error = "Passwords do not match."
            else:
                try:
                    db.create_user(username, generate_password_hash(password, method=PASSWORD_HASH_METHOD))
                except UserExistsError:
                    error = "That username is already taken."
                except ChatDatabaseError:
                    error = "Could not create the account. Please try again."
                else:
                    session.clear()
                    session["username"] = username
                    return redirect(url_for("chat"))
        return render_template("register.html", error=error)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            try:
                user = db.get_user(username)
            except ChatDatabaseError:
                user = None
            # One generic message so attackers cannot tell which part was wrong.
            if user is None or not check_password_hash(user["password_hash"], password):
                error = "Invalid username or password."
            else:
                session.clear()
                session["username"] = user["username"]
                return redirect(url_for("chat"))
        return render_template("login.html", error=error)

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/chat")
    def chat():
        if "username" not in session:
            return redirect(url_for("login"))
        return render_template("chat.html", username=session["username"], default_room=DEFAULT_ROOM)

    @app.route("/api/rooms")
    def api_rooms():
        if "username" not in session:
            return jsonify(error="Not logged in"), 401
        return jsonify(rooms=db.list_rooms())

    # --------------------------------------------------------- Socket.IO events
    def leave_current_room(username):
        room = room_of_session.pop(request.sid, None)
        if room:
            leave_room(room)
            emit("system", {"text": f"{username} left #{room}", "time": _clock()}, to=room)

    @socketio.on("connect")
    def on_connect():
        if "username" not in session:
            return False  # reject: only logged-in users may open a socket
        emit("rooms", {"rooms": db.list_rooms()})

    @socketio.on("join")
    def on_join(data):
        username = session.get("username")
        room = clean_room_name(data.get("room")) if isinstance(data, dict) else None
        if not username:
            return
        if room is None or not db.room_exists(room):
            emit("error_message", {"error": "That room does not exist."})
            return
        leave_current_room(username)
        join_room(room)
        room_of_session[request.sid] = room
        history = [
            {**m, "text": replace_shortcodes(m["text"])} for m in db.get_history(room)
        ]
        emit("history", {"room": room, "messages": history})
        emit("system", {"text": f"{username} joined #{room}", "time": _clock()}, to=room)

    @socketio.on("message")
    def on_message(data):
        username = session.get("username")
        room = room_of_session.get(request.sid)
        if not username:
            return
        if not room:
            emit("error_message", {"error": "Join a room first."})
            return
        text = data.get("text") if isinstance(data, dict) else None
        if not isinstance(text, str) or not text.strip():
            return  # ignore empty messages
        text = text.strip()
        if len(text) > MAX_MESSAGE_LENGTH:
            emit("error_message", {"error": f"Messages can be at most {MAX_MESSAGE_LENGTH} characters."})
            return
        try:
            db.add_message(room, username, text)
        except ChatDatabaseError:
            emit("error_message", {"error": "Your message could not be saved."})
            return
        emit(
            "message",
            {"username": username, "text": replace_shortcodes(text), "time": _clock(), "room": room},
            to=room,
        )

    @socketio.on("create_room")
    def on_create_room(data):
        if "username" not in session:
            return
        name = clean_room_name(data.get("name")) if isinstance(data, dict) else None
        if name is None:
            emit("error_message", {"error": "Room names need 2-30 characters: letters, numbers, - or _."})
            return
        try:
            db.create_room(name)
        except RoomExistsError:
            emit("error_message", {"error": f"Room #{name} already exists."})
            return
        except ChatDatabaseError:
            emit("error_message", {"error": "Could not create the room."})
            return
        socketio.emit("rooms", {"rooms": db.list_rooms()})  # tell everyone
        emit("room_created", {"room": name})

    @socketio.on("disconnect")
    def on_disconnect(*_args):
        room = room_of_session.pop(request.sid, None)
        username = session.get("username")
        if room and username:
            emit("system", {"text": f"{username} disconnected", "time": _clock()}, to=room)

    return app, socketio
