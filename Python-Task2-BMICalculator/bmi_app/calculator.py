"""Pure BMI logic: validation, calculation and classification.

Nothing in this file touches the GUI or the database, so it is easy to test.
"""

MIN_WEIGHT_KG = 1
MAX_WEIGHT_KG = 500
MIN_HEIGHT_M = 0.3
MAX_HEIGHT_M = 2.8


class InvalidInputError(ValueError):
    """Raised when the user's weight, height or name is not acceptable."""


def parse_positive_number(text, field_name):
    """Convert text to a positive float or raise InvalidInputError."""
    text = str(text).strip()
    if not text:
        raise InvalidInputError(f"Please enter your {field_name}.")
    try:
        value = float(text)
    except ValueError:
        raise InvalidInputError(
            f"{field_name.capitalize()} must be a number (for example 70 or 1.75)."
        ) from None
    if value != value or value in (float("inf"), float("-inf")):
        raise InvalidInputError(f"{field_name.capitalize()} must be a real number.")
    if value <= 0:
        raise InvalidInputError(f"{field_name.capitalize()} must be greater than zero.")
    return value


def validate_weight_height(weight_text, height_text):
    """Return (weight_kg, height_m) as floats, or raise InvalidInputError."""
    weight = parse_positive_number(weight_text, "weight")
    height = parse_positive_number(height_text, "height")
    if not MIN_WEIGHT_KG <= weight <= MAX_WEIGHT_KG:
        raise InvalidInputError(
            f"Weight must be between {MIN_WEIGHT_KG} and {MAX_WEIGHT_KG} kg."
        )
    if not MIN_HEIGHT_M <= height <= MAX_HEIGHT_M:
        raise InvalidInputError(
            f"Height must be between {MIN_HEIGHT_M} and {MAX_HEIGHT_M} metres "
            "(for example 1.75, not 175)."
        )
    return weight, height


def calculate_bmi(weight_kg, height_m):
    """BMI = weight / height^2, rounded to 2 decimal places."""
    if weight_kg <= 0 or height_m <= 0:
        raise InvalidInputError("Weight and height must be greater than zero.")
    return round(weight_kg / (height_m ** 2), 2)


def classify_bmi(bmi):
    """Return the standard category for a BMI value.

    The task sheet gives Normal as 18.5-24.9 and Overweight as 25-29.9. We
    compare against the boundaries (18.5, 25, 30) so values such as 24.95
    still fall into exactly one category.
    """
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


# Colours used by the GUI for the colour-coded result.
CATEGORY_COLOURS = {
    "Underweight": "#1e88e5",  # blue
    "Normal": "#2e7d32",       # green
    "Overweight": "#ef6c00",   # orange
    "Obese": "#c62828",        # red
}
