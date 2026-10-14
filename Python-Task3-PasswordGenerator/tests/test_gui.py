"""GUI tests; skipped automatically when no display is available."""

import tkinter as tk

import pytest

from password_app.gui import PasswordApp, copy_to_clipboard


def _display_available():
    try:
        root = tk.Tk()
        root.destroy()
        return True
    except tk.TclError:
        return False


needs_display = pytest.mark.skipif(not _display_available(), reason="no display available")


@pytest.fixture
def app():
    copied = []
    application = PasswordApp(clipboard=lambda text: (copied.append(text) or (True, "Copied to clipboard.")))
    application.copied = copied
    application.withdraw()
    yield application
    application.destroy()


@needs_display
def test_generate_updates_everything_and_auto_copies(app):
    password = app.on_generate()
    assert len(password) == 16
    assert app.password_var.get() == password
    assert app.copied == [password]
    assert "Strength" in app.strength_label.cget("text")
    assert app.history_list.size() == 1


@needs_display
def test_history_never_exceeds_five(app):
    for _ in range(8):
        app.on_generate()
    assert app.history_list.size() == 5


@needs_display
def test_error_shown_in_window_for_bad_length(app):
    # simulate typing into the box (Spinbox.set() would clamp the value)
    app.length_spin.delete(0, "end")
    app.length_spin.insert(0, "3")
    assert app.on_generate() is None
    assert "at least 8" in app.message_var.get()


@needs_display
def test_error_when_fewer_than_two_types(app):
    app.upper_var.set(False)
    app.lower_var.set(False)
    app.digits_var.set(False)
    assert app.on_generate() is None
    assert "at least 2" in app.message_var.get()


@needs_display
def test_copy_button_without_password(app):
    app.on_copy()
    assert "Generate a password first" in app.message_var.get()


@needs_display
def test_clipboard_failure_is_reported_not_raised():
    import pyperclip
    from unittest import mock
    with mock.patch("password_app.gui.pyperclip.copy", side_effect=pyperclip.PyperclipException("no clipboard")):
        ok, message = copy_to_clipboard("secret")
    assert ok is False and "clipboard" in message.lower()


@needs_display
def test_error_shown_for_non_numeric_length(app):
    app.length_spin.delete(0, "end")
    app.length_spin.insert(0, "abc")
    assert app.on_generate() is None
    assert "whole number" in app.message_var.get()
