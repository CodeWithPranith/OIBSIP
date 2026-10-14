"""Entry point: python3 main.py"""

from bmi_app.gui import BMIApp


def main():
    app = BMIApp()
    app.mainloop()


if __name__ == "__main__":
    main()
