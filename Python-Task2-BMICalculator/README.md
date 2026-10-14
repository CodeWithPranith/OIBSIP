# BMI Calculator & Tracker (Python)

**OASIS INFOBYTE Python Programming Internship — Task 2, Advanced tier**

A desktop application (tkinter) that calculates Body Mass Index, shows a colour-coded category, saves records for multiple named users in SQLite, and plots each user's BMI trend with matplotlib.

## Features
- GUI with labelled inputs for name, weight (kg) and height (m) and a **Calculate** button
- BMI = weight / height², rounded to 2 decimals
- Categories: Underweight (< 18.5), Normal (18.5–24.9), Overweight (25–29.9), Obese (≥ 30)
- Colour-coded result: blue = underweight, green = normal, orange = overweight, red = obese
- Input validation: rejects empty, non-numeric, zero, negative, NaN/infinite values and unrealistic ranges (with a hint if you type centimetres)
- Multi-user records saved to SQLite (`~/.bmi_tracker/bmi_records.db`)
- History table for the selected user
- **View Trend** opens a matplotlib line chart of BMI over time, with shaded category bands
- Database errors are caught and shown inside the window

## Technologies
Python 3, tkinter, matplotlib, sqlite3, pytest.

## Project structure
```
Python-Task2-BMICalculator/
├── README.md
├── requirements.txt
├── .gitignore
├── main.py                 # entry point
├── bmi_app/
│   ├── calculator.py       # validation, BMI formula, categories (no GUI)
│   ├── database.py         # SQLite storage
│   └── gui.py              # tkinter window + chart
└── tests/
```

## Installation (macOS)
```bash
cd ~/OIBSIP/Python-Task2-BMICalculator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
tkinter ships with the python.org installer. If you installed Python with Homebrew and see `No module named '_tkinter'`, run `brew install python-tk`.

## Run
```bash
python3 main.py
```

## Run the tests
```bash
python3 -m pytest -v
```
GUI tests need a display; they run on your Mac and are skipped automatically on a headless machine.

## Example usage
1. Type a name (for example `Asha`), weight `70`, height `1.75`.
2. Click **Calculate** → `BMI: 22.86 (Normal)` on a green background.
3. Click **Save Record**. Repeat on other days (or with other names).
4. Click **View Trend** to see the chart.

## Limitations
- Height must be in metres, weight in kilograms.
- BMI is a general screening number, not medical advice; it does not account for muscle mass, age or sex.
- Records are identified by name only (no passwords).
- Records cannot be edited or deleted from the GUI.

## Future improvements
- Edit/delete records, export to CSV
- Imperial units
- Separate user profiles with passwords
