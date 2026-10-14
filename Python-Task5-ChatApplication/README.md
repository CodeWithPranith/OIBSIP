# Chat Application (Python)

**OASIS INFOBYTE Python Programming Internship — Task 5, Advanced tier**

A real-time chat application in two parts:

1. **Beginner tier** – a command-line chat built directly on TCP sockets and threads (`beginner_socket_chat/`).
2. **Advanced tier** – a browser-based chat built with Flask and Flask-SocketIO, with user accounts, multiple rooms, saved message history, emoji shortcodes and desktop notifications (`web_chat/`).

## Features

### Beginner (sockets)
- Server that listens for connections; client that connects to it
- Real-time two-way messaging (works for two or more clients)
- Timestamped messages, for example `[14:35] Alice: Hello`
- Join and disconnect notices; clean handling of dropped connections
- Runs on one machine using `localhost`

### Advanced (web)
- Browser chat window (HTML/CSS/JavaScript served by Flask)
- Registration and login (username + password, stored in SQLite, password hashed with PBKDF2-SHA256)
- Create and join named rooms; rooms are isolated from each other
- Message history: the last 50 messages of a room are loaded when you join
- Browser notifications (and an unread counter in the tab title) for new messages while the window is not focused
- Emoji shortcodes such as `:smile:` are shown as 😄
- Input validation, parameterised SQL queries, and escaped output (messages are rendered with `textContent`)

## Technologies
Python 3, `socket`, `threading`, Flask, Flask-SocketIO, SQLite (`sqlite3`), Werkzeug password hashing, HTML/CSS/JavaScript, pytest.

## Project structure
```
Python-Task5-ChatApplication/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── run_web.py                     # starts the web chat
├── beginner_socket_chat/
│   ├── common.py                  # host/port + timestamp formatting
│   ├── chat_server.py             # TCP server
│   └── chat_client.py             # TCP client
├── web_chat/
│   ├── app.py                     # Flask routes + Socket.IO events
│   ├── database.py                # SQLite (users, rooms, messages)
│   ├── emoji_map.py               # :shortcode: -> emoji
│   ├── templates/                 # login, register, chat pages
│   └── static/                    # style.css, chat.js
└── tests/                         # pytest tests
```

## Installation (macOS)
```bash
cd ~/OIBSIP/Python-Task5-ChatApplication
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration
Optional: set a fixed secret key for session cookies (otherwise a random one is created on every start, which logs everyone out after a restart):
```bash
export CHAT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```
See `.env.example`. Never commit real secrets.

## Running

### Advanced web chat
```bash
python3 run_web.py
```
Open <http://127.0.0.1:5001> in your browser, register, and chat. To test with two users, open a second browser or a private window and register another account. Stop the server with `Ctrl+C`.
Port 5001 is used because macOS AirPlay Receiver often occupies port 5000.
The page loads the Socket.IO JavaScript library from a CDN, so an internet connection is needed.

### Beginner socket chat (three Terminal windows)
```bash
# Window 1 - server
python3 -m beginner_socket_chat.chat_server
# Window 2
python3 -m beginner_socket_chat.chat_client --name Alice
# Window 3
python3 -m beginner_socket_chat.chat_client --name Bob
```
Type a message and press Enter. Type `/quit` to leave.

## Running the tests
```bash
python3 -m pytest -v
```

## Example usage
```
[14:35] * Bob has joined the chat
[14:36] Bob: Hello Alice
[14:36] Alice: Hi Bob!
[14:40] * Bob has disconnected
```

## Security and privacy transparency (what is and is not protected)
- **Messages are stored in plain text** in the SQLite file `chat.db` (in the project folder). Anyone with access to that file can read every message. There is **no end-to-end encryption**.
- **Traffic is not encrypted in transit.** The web chat runs over plain HTTP and the socket chat over plain TCP. This is acceptable for `localhost`, but not for use over a network or the internet. Real deployments need HTTPS/WSS.
- **Passwords are never stored in plain text** – only salted PBKDF2-SHA256 hashes.
- Login sessions use a signed, HTTP-only cookie. Only logged-in users can open a Socket.IO connection.
- Not implemented: CSRF tokens on the forms, login rate limiting, message editing/deleting, private rooms. The socket chat has no authentication at all.

## Limitations
- Designed for local demonstration, not production use (Flask development server).
- Notifications require the user to click "Enable notifications" and allow them in the browser.
- The automated tests use Flask-SocketIO's test client; they do not drive a real browser.

## Future improvements
- HTTPS, CSRF protection, rate limiting
- Private rooms and direct messages
- Message pagination ("load older messages")
- File/image sharing
