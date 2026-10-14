"""Entry point.

  python3 main.py        -> opens the GUI
  python3 main.py --cli  -> command-line version
"""

import sys


def main():
    if "--cli" in sys.argv[1:]:
        from password_app.cli import run_cli
        run_cli()
    else:
        from password_app.gui import PasswordApp
        PasswordApp().mainloop()


if __name__ == "__main__":
    main()
