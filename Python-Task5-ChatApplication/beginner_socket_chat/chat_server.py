"""TCP chat server. Run with:  python3 -m beginner_socket_chat.chat_server

Protocol (plain text, one message per line):
  1. the client sends its username as the first line
  2. every later line is a chat message, which the server forwards to all
     other connected clients with a timestamp.
"""

import argparse
import socket
import threading
import time

from .common import DEFAULT_HOST, DEFAULT_PORT, format_message, system_message

MAX_LINE_BYTES = 2048


class ChatServer:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self._clients = {}  # socket -> username (only fully registered clients)
        self._lock = threading.Lock()
        self._server_socket = None
        self._running = threading.Event()

    # ----- lifecycle -----
    def start(self):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen()
        self.port = self._server_socket.getsockname()[1]  # real port if 0 was requested
        self._running.set()
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def stop(self):
        self._running.clear()
        if self._server_socket:
            self._server_socket.close()
        with self._lock:
            sockets = list(self._clients)
        for client in sockets:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            client.close()

    # ----- internals -----
    def _accept_loop(self):
        while self._running.is_set():
            try:
                connection, _address = self._server_socket.accept()
            except OSError:
                break  # server socket was closed by stop()
            threading.Thread(target=self._handle_client, args=(connection,), daemon=True).start()

    def _send(self, connection, text):
        try:
            connection.sendall((text + "\n").encode("utf-8"))
        except OSError:
            pass  # that client's own thread will notice the broken connection

    def _broadcast(self, text, exclude=None):
        with self._lock:
            targets = [c for c in self._clients if c is not exclude]
        for connection in targets:
            self._send(connection, text)

    def _handle_client(self, connection):
        username = None
        try:
            reader = connection.makefile("r", encoding="utf-8", errors="replace", newline="\n")
            username = reader.readline(MAX_LINE_BYTES).strip()
            if not username:
                return
            with self._lock:
                taken = username in self._clients.values()
                if not taken:
                    self._clients[connection] = username
            if taken:
                self._send(connection, system_message(f"The name '{username}' is already in use."))
                username = None  # not registered, so no 'disconnected' notice later
                return
            self._send(connection, system_message(f"Welcome, {username}! Type /quit to leave."))
            self._broadcast(system_message(f"{username} has joined the chat"), exclude=connection)
            for line in iter(lambda: reader.readline(MAX_LINE_BYTES), ""):
                text = line.strip()
                if text:
                    self._broadcast(format_message(username, text), exclude=connection)
        except (OSError, ValueError):
            pass  # connection dropped abruptly
        finally:
            with self._lock:
                was_registered = self._clients.pop(connection, None) is not None
            if was_registered:
                self._broadcast(system_message(f"{username} has disconnected"))
            connection.close()


def main():
    parser = argparse.ArgumentParser(description="Simple TCP chat server")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    server = ChatServer(args.host, args.port)
    try:
        server.start()
    except OSError as exc:
        print(f"Could not start the server on {args.host}:{args.port}: {exc}")
        return 1
    print(f"Chat server listening on {server.host}:{server.port}. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
