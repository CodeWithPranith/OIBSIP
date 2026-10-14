# Random Password Generator (Python)

**OASIS INFOBYTE Python Programming Internship — Task 3, Advanced tier**

A password generator with a tkinter GUI that uses Python's cryptographically secure `secrets` module. A command-line mode is included for the Beginner-tier workflow.

## Features
- Length control with a **spinbox and a slider** (8–64 characters, minimum 8 enforced)
- Checkboxes for uppercase, lowercase, numbers and symbols (**at least 2 types required**)
- Uses `secrets`, **not** `random`
- Guarantees at least one character from every selected type
- Option to exclude ambiguous characters (`0 O 1 l I |`)
- Strength indicator: progress bar plus Weak / Medium / Strong label (based on length and character variety, via an entropy estimate)
- **Copy to Clipboard** button; the password is also copied automatically when generated (`pyperclip`)
- Shows the last 5 passwords of the session — kept in memory only, never written to disk
- Errors are shown inside the window
- `--cli` mode: prompts for length and character types and offers to generate another password

## Technologies
Python 3, tkinter, secrets, pyperclip, pytest.

## Project structure
```
Python-Task3-PasswordGenerator/
├── README.md
├── requirements.txt
├── .gitignore
├── main.py                  # entry point (GUI, or --cli)
├── password_app/
│   ├── generator.py         # generation, strength, history (no GUI)
│   ├── cli.py               # command-line version
│   └── gui.py               # tkinter window
└── tests/
```

## Installation (macOS)
```bash
cd ~/OIBSIP/Python-Task3-PasswordGenerator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
If you see `No module named '_tkinter'` (Homebrew Python): `brew install python-tk`.

## Run
```bash
python3 main.py          # GUI
python3 main.py --cli    # command line
```

## Run the tests
```bash
python3 -m pytest -v
```
GUI tests need a display; they run on your Mac and are skipped automatically on a headless machine.

## Example usage
Choose length 16, keep all four boxes ticked, click **Generate Password**. A password appears, the bar shows its strength, and it is already on your clipboard – paste it anywhere with Cmd+V.

## Security notes
- `secrets` draws from the operating system's secure random source.
- History is deliberately not saved to a file.
- Anything copied to the clipboard stays there until you copy something else; some clipboard managers keep a history.

## Limitations
- The strength rating is an estimate from length and character variety. It cannot detect common words or patterns, which only matter for human-chosen passwords.
- The clipboard feature depends on `pyperclip` finding a clipboard tool (works with `pbcopy` on macOS); otherwise the window shows an error message.

## Future improvements
- Passphrase mode (random words)
- Auto-clear the clipboard after 30 seconds
- Save settings between sessions
