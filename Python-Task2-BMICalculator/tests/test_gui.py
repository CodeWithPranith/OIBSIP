"""GUI tests. They need a display, so they are skipped when none is available
(for example on a headless server). On a Mac they run normally."""

import tkinter as tk

import pytest

from bmi_app.database import BMIDatabase
from bmi_app.gui import BMIApp, build_trend_figure


def _display_available():
    try:
        root = tk.Tk()
        root.destroy()
        return True
    except tk.TclError:
        return False


needs_display = pytest.mark.skipif(not _display_available(), reason="no display available")


def test_trend_figure_has_one_point_per_record():
    history = [
        {"bmi": 22.0, "recorded_at": "2026-01-01T10:00:00"},
        {"bmi": 23.5, "recorded_at": "2026-02-01T10:00:00"},
        {"bmi": 26.1, "recorded_at": "2026-03-01T10:00:00"},
    ]
    figure = build_trend_figure(history, "Asha")
    line = figure.axes[0].lines[0]
    assert list(line.get_ydata()) == [22.0, 23.5, 26.1]


@pytest.fixture
def app(tmp_path):
    application = BMIApp(BMIDatabase(tmp_path / "gui.db"))
    application.withdraw()
    yield application
    application.destroy()


@needs_display
def test_calculate_shows_result_and_colour(app):
    app.weight_var.set("70")
    app.height_var.set("1.75")
    app.on_calculate()
    assert "22.86" in app.result_label.cget("text")
    assert "Normal" in app.result_label.cget("text")
    assert app.result_label.cget("bg") == "#2e7d32"


@needs_display
def test_invalid_input_shows_error_in_window(app):
    app.weight_var.set("abc")
    app.height_var.set("1.75")
    app.on_calculate()
    assert "number" in app.message_var.get()


@needs_display
def test_save_requires_name(app):
    app.weight_var.set("70")
    app.height_var.set("1.75")
    app.on_save()
    assert "name" in app.message_var.get().lower()
    assert app.db.get_users() == []
