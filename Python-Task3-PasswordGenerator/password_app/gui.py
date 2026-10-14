"""Tkinter user interface for the password generator."""

import tkinter as tk
from tkinter import ttk

import pyperclip

from .generator import (
    MAX_LENGTH,
    MIN_LENGTH,
    PasswordConfigError,
    PasswordHistory,
    estimate_strength,
    generate_password,
)

STRENGTH_COLOURS = {"Weak": "#c62828", "Medium": "#ef6c00", "Strong": "#2e7d32"}


def copy_to_clipboard(text):
    """Copy text using pyperclip. Returns (success, message)."""
    try:
        pyperclip.copy(text)
        return True, "Copied to clipboard."
    except pyperclip.PyperclipException:
        return False, "Could not access the clipboard on this system."


class PasswordApp(tk.Tk):
    def __init__(self, clipboard=copy_to_clipboard):
        super().__init__()
        self.title("Secure Password Generator")
        self.resizable(False, False)
        self._copy = clipboard
        self.history = PasswordHistory()
        self._build_widgets()

    def _build_widgets(self):
        frame = ttk.Frame(self, padding=16)
        frame.grid()

        # --- length: spinbox and slider share one variable ---
        ttk.Label(frame, text="Length:").grid(row=0, column=0, sticky="w")
        self.length_var = tk.IntVar(value=16)
        self.length_spin = ttk.Spinbox(frame, from_=MIN_LENGTH, to=MAX_LENGTH, textvariable=self.length_var, width=5)
        self.length_spin.grid(row=0, column=1, sticky="w")
        self.length_scale = ttk.Scale(frame, from_=MIN_LENGTH, to=MAX_LENGTH, orient="horizontal", length=220,
                                      command=lambda v: self.length_var.set(int(float(v))))
        self.length_scale.set(16)
        self.length_scale.grid(row=1, column=0, columnspan=3, pady=(2, 10), sticky="w")

        # --- character type checkboxes ---
        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)
        self.ambiguous_var = tk.BooleanVar(value=False)
        options = [("Uppercase (A-Z)", self.upper_var), ("Lowercase (a-z)", self.lower_var),
                   ("Numbers (0-9)", self.digits_var), ("Symbols (!@#...)", self.symbols_var),
                   ("Exclude ambiguous (0 O 1 l I |)", self.ambiguous_var)]
        for i, (text, var) in enumerate(options):
            ttk.Checkbutton(frame, text=text, variable=var).grid(row=2 + i, column=0, columnspan=3, sticky="w")

        ttk.Button(frame, text="Generate Password", command=self.on_generate).grid(row=7, column=0, columnspan=3, pady=10, sticky="ew")

        # --- output ---
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(frame, textvariable=self.password_var, font=("Courier", 14), width=34, state="readonly")
        self.password_entry.grid(row=8, column=0, columnspan=3, pady=4)
        ttk.Button(frame, text="Copy to Clipboard", command=self.on_copy).grid(row=9, column=0, columnspan=3, pady=4, sticky="ew")

        # --- strength indicator ---
        self.strength_bar = ttk.Progressbar(frame, maximum=100, length=300)
        self.strength_bar.grid(row=10, column=0, columnspan=3, pady=(8, 0))
        self.strength_label = tk.Label(frame, text="Strength: -", font=("Helvetica", 12, "bold"))
        self.strength_label.grid(row=11, column=0, columnspan=3)

        self.message_var = tk.StringVar()
        self.message_label = tk.Label(frame, textvariable=self.message_var, wraplength=320, fg="#c62828")
        self.message_label.grid(row=12, column=0, columnspan=3, pady=4)

        ttk.Label(frame, text="Last 5 passwords (this session only):").grid(row=13, column=0, columnspan=3, sticky="w", pady=(8, 2))
        self.history_list = tk.Listbox(frame, height=5, width=40, font=("Courier", 11))
        self.history_list.grid(row=14, column=0, columnspan=3)

        self.length_var.trace_add("write", lambda *_: self._sync_scale())

    def _sync_scale(self):
        """Move the slider when the spinbox value changes.

        Out-of-range or half-typed values are ignored here on purpose, so the
        generator's validation can show its own error message for them.
        """
        try:
            value = int(self.length_var.get())
        except (tk.TclError, ValueError):
            return
        if MIN_LENGTH <= value <= MAX_LENGTH and int(float(self.length_scale.get())) != value:
            self.length_scale.set(value)

    def _show_message(self, text, error=True):
        self.message_label.config(fg="#c62828" if error else "#2e7d32")
        self.message_var.set(text)

    def on_generate(self):
        """Generate a password, show strength, store in history, auto-copy."""
        try:
            length = self.length_spin.get()
            password = generate_password(
                length, self.upper_var.get(), self.lower_var.get(),
                self.digits_var.get(), self.symbols_var.get(), self.ambiguous_var.get(),
            )
        except PasswordConfigError as exc:
            self._show_message(str(exc))
            return None
        self.password_var.set(password)
        self.history.add(password)
        self._refresh_history()
        label, fraction, bits = estimate_strength(password)
        self.strength_bar["value"] = fraction * 100
        self.strength_label.config(text=f"Strength: {label} ({bits} bits)", fg=STRENGTH_COLOURS[label])
        ok, message = self._copy(password)  # copies automatically on generation
        self._show_message(message, error=not ok)
        return password

    def on_copy(self):
        password = self.password_var.get()
        if not password:
            self._show_message("Generate a password first.")
            return
        ok, message = self._copy(password)
        self._show_message(message, error=not ok)

    def _refresh_history(self):
        self.history_list.delete(0, "end")
        for item in self.history.items():
            self.history_list.insert("end", item)
