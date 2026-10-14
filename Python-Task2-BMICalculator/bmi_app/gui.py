"""Tkinter user interface for the BMI tracker."""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .calculator import (
    CATEGORY_COLOURS,
    InvalidInputError,
    calculate_bmi,
    classify_bmi,
    validate_weight_height,
)
from .database import BMIDatabase, DatabaseError


def build_trend_figure(history, user_name):
    """Create a matplotlib Figure with the user's BMI over time.

    Kept separate from the window code so it can be tested without a display.
    """
    figure = Figure(figsize=(6.5, 4), dpi=100)
    axes = figure.add_subplot(111)
    dates = [datetime.fromisoformat(r["recorded_at"]) for r in history]
    values = [r["bmi"] for r in history]
    axes.plot(dates, values, marker="o", color="#1565c0")
    # Shaded bands make it obvious which health category each point falls in.
    axes.axhspan(0, 18.5, color=CATEGORY_COLOURS["Underweight"], alpha=0.08)
    axes.axhspan(18.5, 25, color=CATEGORY_COLOURS["Normal"], alpha=0.10)
    axes.axhspan(25, 30, color=CATEGORY_COLOURS["Overweight"], alpha=0.10)
    axes.axhspan(30, 60, color=CATEGORY_COLOURS["Obese"], alpha=0.08)
    low, high = min(values + [18.5]) - 2, max(values + [30]) + 2
    axes.set_ylim(low, high)
    axes.set_title(f"BMI trend for {user_name}")
    axes.set_xlabel("Date")
    axes.set_ylabel("BMI")
    axes.grid(alpha=0.3)
    figure.autofmt_xdate()
    figure.tight_layout()
    return figure


class BMIApp(tk.Tk):
    def __init__(self, database=None):
        super().__init__()
        self.title("BMI Calculator & Tracker")
        self.resizable(False, False)
        try:
            self.db = database or BMIDatabase()
        except DatabaseError as exc:
            messagebox.showerror("Database error", str(exc))
            self.destroy()
            raise
        self._build_widgets()
        self._refresh_users()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- layout ----------
    def _build_widgets(self):
        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0)

        ttk.Label(frame, text="Name:").grid(row=0, column=0, sticky="e", pady=4)
        self.name_var = tk.StringVar()
        self.name_box = ttk.Combobox(frame, textvariable=self.name_var, width=24)
        self.name_box.grid(row=0, column=1, pady=4, padx=6)

        ttk.Label(frame, text="Weight (kg):").grid(row=1, column=0, sticky="e", pady=4)
        self.weight_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.weight_var, width=26).grid(row=1, column=1, pady=4, padx=6)

        ttk.Label(frame, text="Height (m):").grid(row=2, column=0, sticky="e", pady=4)
        self.height_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.height_var, width=26).grid(row=2, column=1, pady=4, padx=6)

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(buttons, text="Calculate", command=self.on_calculate).pack(side="left", padx=4)
        ttk.Button(buttons, text="Save Record", command=self.on_save).pack(side="left", padx=4)
        ttk.Button(buttons, text="View Trend", command=self.on_view_trend).pack(side="left", padx=4)

        self.result_label = tk.Label(frame, text="Enter your details above.", font=("Helvetica", 16, "bold"), width=30, pady=10)
        self.result_label.grid(row=4, column=0, columnspan=2, pady=4)

        self.message_var = tk.StringVar()
        self.message_label = ttk.Label(frame, textvariable=self.message_var, foreground="#c62828", wraplength=340)
        self.message_label.grid(row=5, column=0, columnspan=2)

        ttk.Label(frame, text="History for selected name:").grid(row=6, column=0, columnspan=2, sticky="w", pady=(10, 2))
        columns = ("date", "weight", "height", "bmi", "category")
        self.history_table = ttk.Treeview(frame, columns=columns, show="headings", height=6)
        for column, title, width in [("date", "Date", 140), ("weight", "kg", 55), ("height", "m", 55), ("bmi", "BMI", 60), ("category", "Category", 90)]:
            self.history_table.heading(column, text=title)
            self.history_table.column(column, width=width, anchor="center")
        self.history_table.grid(row=7, column=0, columnspan=2)
        self.name_box.bind("<<ComboboxSelected>>", lambda _e: self._refresh_history())

        self.last_result = None  # (weight, height, bmi, category) of last Calculate

    # ---------- actions ----------
    def _show_error(self, text):
        self.message_var.set(text)

    def on_calculate(self):
        """Validate input, compute BMI and show a colour-coded result."""
        self.message_var.set("")
        try:
            weight, height = validate_weight_height(self.weight_var.get(), self.height_var.get())
        except InvalidInputError as exc:
            self.last_result = None
            self._show_error(str(exc))
            return None
        bmi = calculate_bmi(weight, height)
        category = classify_bmi(bmi)
        self.last_result = (weight, height, bmi, category)
        self.result_label.config(text=f"BMI: {bmi:.2f}  ({category})", fg="white", bg=CATEGORY_COLOURS[category])
        return self.last_result

    def on_save(self):
        """Calculate (to make sure the numbers are current) and store the record."""
        result = self.on_calculate()
        if result is None:
            return
        name = self.name_var.get().strip()
        if not name:
            self._show_error("Enter a name so the record can be saved.")
            return
        try:
            self.db.save_record(name, *result)
        except DatabaseError as exc:
            self._show_error(str(exc))
            return
        self._refresh_users()
        self._refresh_history()
        self.message_var.set("")
        messagebox.showinfo("Saved", f"Record saved for {name}.")

    def on_view_trend(self):
        name = self.name_var.get().strip()
        if not name:
            self._show_error("Select or type a name to view a trend.")
            return
        try:
            history = self.db.get_history(name)
        except DatabaseError as exc:
            self._show_error(str(exc))
            return
        if not history:
            self._show_error(f"No saved records for '{name}' yet.")
            return
        window = tk.Toplevel(self)
        window.title(f"BMI trend - {name}")
        canvas = FigureCanvasTkAgg(build_trend_figure(history, name), master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---------- helpers ----------
    def _refresh_users(self):
        try:
            self.name_box["values"] = self.db.get_users()
        except DatabaseError as exc:
            self._show_error(str(exc))

    def _refresh_history(self):
        self.history_table.delete(*self.history_table.get_children())
        name = self.name_var.get().strip()
        if not name:
            return
        try:
            history = self.db.get_history(name)
        except DatabaseError as exc:
            self._show_error(str(exc))
            return
        for row in history:
            self.history_table.insert("", "end", values=(row["recorded_at"].replace("T", " "), row["weight_kg"], row["height_m"], f"{row['bmi']:.2f}", row["category"]))

    def _on_close(self):
        self.db.close()
        self.destroy()
