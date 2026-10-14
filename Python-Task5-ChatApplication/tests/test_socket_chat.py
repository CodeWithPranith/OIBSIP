import re
import socket
import time

import pytest

from beginner_socket_chat.chat_server import ChatServer
from beginner_socket_chat.common import format_message, system_message

TIMESTAMP = re.compile(r"^\[\d{2}:\d{2}\] ")


@pytest.fixture
def server():
    chat_server = ChatServer("127.0.0.1", 0)  # port 0 = let the OS pick a free port
    chat_server.start()
    yield chat_server
    chat_server.stop()


class RawClient:
    """Tiny raw-socket client used only by the tests."""

    def __init__(self, port, name):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=3)
        self.reader = self.sock.makefile("r", encoding="utf-8", newline="\n")
        self.sock.sendall((name + "\n").encode())

    def send(self, text):
        self.sock.sendall((text + "\n").encode())

    def read_line(self):
        return self.reader.readline().rstrip("\n")

    def close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)  # makefile() keeps the socket open otherwise
        except OSError:
            pass
        self.sock.close()


def connect_two(server):
    alice = RawClient(server.port, "Alice")
    assert "Welcome, Alice" in alice.read_line()
    bob = RawClient(server.port, "Bob")
    assert "Welcome, Bob" in bob.read_line()
    assert "Bob has joined" in alice.read_line()
    return alice, bob


def test_format_message_matches_task_example():
    from datetime import datetime
    assert format_message("Alice", "Hello", datetime(2026, 1, 1, 14, 35)) == "[14:35] Alice: Hello"


def test_system_message_has_timestamp():
    assert TIMESTAMP.match(system_message("hi"))


def test_message_goes_both_directions_with_timestamp(server):
    alice, bob = connect_two(server)
    alice.send("Hello Bob")
    line = bob.read_line()
    assert TIMESTAMP.match(line) and line.endswith("Alice: Hello Bob")
    bob.send("Hi Alice")
    line = alice.read_line()
    assert TIMESTAMP.match(line) and line.endswith("Bob: Hi Alice")
    alice.close(); bob.close()


def test_sender_does_not_receive_own_message(server):
    alice, bob = connect_two(server)
    alice.send("only bob should see this")
    assert "only bob" in bob.read_line()
    bob.send("reply")
    # Alice's very next line must be Bob's reply, not an echo of her own message
    assert alice.read_line().endswith("Bob: reply")
    alice.close(); bob.close()


def test_disconnect_notifies_other_client(server):
    alice, bob = connect_two(server)
    bob.close()
    assert "Bob has disconnected" in alice.read_line()
    alice.close()


def test_duplicate_username_rejected(server):
    alice = RawClient(server.port, "Alice")
    alice.read_line()
    imposter = RawClient(server.port, "Alice")
    assert "already in use" in imposter.read_line()
    assert imposter.read_line() == ""  # server closed the connection
    # the original Alice must not be reported as disconnected
    bob = RawClient(server.port, "Bob")
    bob.read_line()
    assert "Bob has joined" in alice.read_line()
    alice.close(); bob.close(); imposter.close()


def test_blank_messages_are_ignored(server):
    alice, bob = connect_two(server)
    alice.send("   ")
    alice.send("real")
    assert bob.read_line().endswith("Alice: real")
    alice.close(); bob.close()


def test_server_survives_abrupt_client_drop(server):
    alice, bob = connect_two(server)
    bob.sock.shutdown(socket.SHUT_RDWR)
    assert "Bob has disconnected" in alice.read_line()
    carol = RawClient(server.port, "Carol")
    assert "Welcome, Carol" in carol.read_line()
    alice.close(); carol.close()


def test_client_reports_unreachable_server(capsys):
    from beginner_socket_chat.chat_client import run_client
    # port 1 on localhost is almost certainly closed
    assert run_client("127.0.0.1", 1, "Zed") == 1
    assert "Is the server running" in capsys.readouterr().out


def test_client_script_sends_and_quits(server, capsys):
    from beginner_socket_chat.chat_client import run_client
    bob = RawClient(server.port, "Bob")
    bob.read_line()
    answers = iter(["hello from client", "/quit"])
    code = run_client("127.0.0.1", server.port, "Dana", lambda: next(answers))
    assert code == 0
    lines = []
    for _ in range(3):
        lines.append(bob.read_line())
    assert any("Dana has joined" in l for l in lines)
    assert any(l.endswith("Dana: hello from client") for l in lines)
    assert any("Dana has disconnected" in l for l in lines)
    bob.close()
