"""Settings and message formatting shared by the socket server and client."""

from datetime import datetime

DEFAULT_HOST = "127.0.0.1"  # localhost: both scripts run on the same machine
DEFAULT_PORT = 5050


def format_message(username, text, when=None):
    """Return a chat line such as '[14:35] Alice: Hello'."""
    when = when or datetime.now()
    return f"[{when.strftime('%H:%M')}] {username}: {text}"


def system_message(text, when=None):
    """Return a notice such as '[14:35] * Bob has disconnected'."""
    when = when or datetime.now()
    return f"[{when.strftime('%H:%M')}] * {text}"
