"""TCP chat client. Run with:  python3 -m beginner_socket_chat.chat_client"""

import argparse
import socket
import threading

from .common import DEFAULT_HOST, DEFAULT_PORT, format_message

# Moves the cursor up one line and clears it, so our typed line is replaced by
# the same line with a timestamp.
ERASE_PREVIOUS_LINE = "\033[A\033[2K"


def run_client(host, port, username, input_fn=input):
    """Connect and chat until the user types /quit. Returns an exit code."""
    try:
        connection = socket.create_connection((host, port), timeout=5)
    except OSError as exc:
        print(f"Could not connect to {host}:{port} ({exc}). Is the server running?")
        return 1
    connection.settimeout(None)
    connection.sendall((username + "\n").encode("utf-8"))
    reader = connection.makefile("r", encoding="utf-8", errors="replace", newline="\n")
    server_closed = threading.Event()
    leaving = threading.Event()  # set when WE decide to quit

    def receive_loop():
        for line in reader:  # ends when the server closes the connection
            print(line.rstrip("\n"))
        if not leaving.is_set():
            print("* The connection to the server was closed. Press Enter to exit.")
        server_closed.set()

    threading.Thread(target=receive_loop, daemon=True).start()
    try:
        while not server_closed.is_set():
            text = input_fn().strip()
            if text == "/quit":
                break
            if text:
                connection.sendall((text + "\n").encode("utf-8"))
                print(ERASE_PREVIOUS_LINE + format_message(username, text))
    except (EOFError, KeyboardInterrupt):
        print()
    except OSError:
        print("* Lost connection to the server.")
    finally:
        leaving.set()
        # close() alone is not enough: the makefile() reader still holds the
        # socket open. shutdown() tells the server we are leaving right now.
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        connection.close()
    return 0


def main():
    parser = argparse.ArgumentParser(description="Simple TCP chat client")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--name", help="your display name")
    args = parser.parse_args()
    name = (args.name or input("Your name: ")).strip()
    if not name:
        print("A name is required.")
        return 1
    return run_client(args.host, args.port, name)


if __name__ == "__main__":
    raise SystemExit(main())
