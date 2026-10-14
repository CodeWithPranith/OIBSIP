"""Password generation, strength rating and session history.

Only the `secrets` module is used for randomness. `random` is NOT suitable
for passwords because its output can be predicted if an attacker learns
enough of its internal state.
"""

import math
import secrets
import string
from collections import deque

MIN_LENGTH = 8
MAX_LENGTH = 64
HISTORY_SIZE = 5

UPPERCASE = string.ascii_uppercase
LOWERCASE = string.ascii_lowercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?/~"
# Characters that are easy to mix up when reading a password aloud or on paper.
AMBIGUOUS = "0O1lI|"


class PasswordConfigError(ValueError):
    """Raised when the requested password settings are not valid."""


def build_character_sets(use_upper, use_lower, use_digits, use_symbols, exclude_ambiguous=False):
    """Return a list of the selected character sets (one string per type)."""
    chosen = []
    if use_upper:
        chosen.append(UPPERCASE)
    if use_lower:
        chosen.append(LOWERCASE)
    if use_digits:
        chosen.append(DIGITS)
    if use_symbols:
        chosen.append(SYMBOLS)
    if exclude_ambiguous:
        chosen = ["".join(c for c in charset if c not in AMBIGUOUS) for charset in chosen]
    return chosen


def validate_length(length):
    """Return length as an int or raise PasswordConfigError."""
    if isinstance(length, bool):
        raise PasswordConfigError("Length must be a whole number.")
    try:
        number = int(str(length).strip())
    except (TypeError, ValueError):
        raise PasswordConfigError("Length must be a whole number.") from None
    if number < MIN_LENGTH:
        raise PasswordConfigError(f"Length must be at least {MIN_LENGTH} characters.")
    if number > MAX_LENGTH:
        raise PasswordConfigError(f"Length must be at most {MAX_LENGTH} characters.")
    return number


def _secure_shuffle(items):
    """Fisher-Yates shuffle driven by secrets.randbelow (in place)."""
    for i in range(len(items) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        items[i], items[j] = items[j], items[i]


def generate_password(length, use_upper=True, use_lower=True, use_digits=True,
                      use_symbols=True, exclude_ambiguous=False):
    """Generate a password that contains at least one character of every
    selected type. Raises PasswordConfigError for invalid settings."""
    length = validate_length(length)
    charsets = build_character_sets(use_upper, use_lower, use_digits, use_symbols, exclude_ambiguous)
    if len(charsets) < 2:
        raise PasswordConfigError("Select at least 2 character types.")

    # 1) guarantee one character from each selected type
    characters = [secrets.choice(charset) for charset in charsets]
    # 2) fill the rest from the combined pool
    pool = "".join(charsets)
    characters += [secrets.choice(pool) for _ in range(length - len(characters))]
    # 3) shuffle so the guaranteed characters are not always at the start
    _secure_shuffle(characters)
    return "".join(characters)


def estimate_strength(password):
    """Rate a password as Weak / Medium / Strong.

    The rating uses the length and the variety of character types (together
    they give the entropy estimate length * log2(pool size)).
    Returns (label, fraction_between_0_and_1, entropy_bits).
    """
    pool = 0
    if any(c in string.ascii_lowercase for c in password):
        pool += 26
    if any(c in string.ascii_uppercase for c in password):
        pool += 26
    if any(c in string.digits for c in password):
        pool += 10
    if any(not c.isalnum() for c in password):
        pool += 32
    if not password or pool == 0:
        return "Weak", 0.0, 0.0
    entropy = len(password) * math.log2(pool)
    if entropy < 50:
        label = "Weak"
    elif entropy < 75:
        label = "Medium"
    else:
        label = "Strong"
    return label, min(entropy / 100, 1.0), round(entropy, 1)


class PasswordHistory:
    """Keeps the last few passwords IN MEMORY ONLY (never written to disk)."""

    def __init__(self, size=HISTORY_SIZE):
        self._items = deque(maxlen=size)

    def add(self, password):
        self._items.appendleft(password)

    def items(self):
        """Newest first."""
        return list(self._items)
