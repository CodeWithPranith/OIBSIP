"""Command-line version of the generator (the Beginner-tier workflow)."""

from .generator import (
    MAX_LENGTH,
    MIN_LENGTH,
    PasswordConfigError,
    estimate_strength,
    generate_password,
)


def _ask_yes_no(prompt, input_fn):
    while True:
        answer = input_fn(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer y or n.")


def run_cli(input_fn=input):
    """Interactive loop. `input_fn` can be replaced in tests."""
    print("=== Random Password Generator ===")
    while True:
        try:
            length = input_fn(f"Password length ({MIN_LENGTH}-{MAX_LENGTH}): ")
            use_upper = _ask_yes_no("Include uppercase letters? (y/n): ", input_fn)
            use_lower = _ask_yes_no("Include lowercase letters? (y/n): ", input_fn)
            use_digits = _ask_yes_no("Include numbers? (y/n): ", input_fn)
            use_symbols = _ask_yes_no("Include symbols? (y/n): ", input_fn)
            password = generate_password(length, use_upper, use_lower, use_digits, use_symbols)
        except PasswordConfigError as exc:
            print(f"Error: {exc}")
        else:
            label, _fraction, _bits = estimate_strength(password)
            print(f"\nYour password: {password}\nStrength: {label}\n")
        if not _ask_yes_no("Generate another password? (y/n): ", input_fn):
            print("Goodbye!")
            return
