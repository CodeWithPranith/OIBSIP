import pytest

from bmi_app.calculator import (
    InvalidInputError,
    calculate_bmi,
    classify_bmi,
    parse_positive_number,
    validate_weight_height,
)


def test_calculate_bmi_normal_case():
    assert calculate_bmi(70, 1.75) == 22.86


def test_calculate_bmi_rounds_to_two_decimals():
    assert calculate_bmi(80, 1.8) == 24.69


@pytest.mark.parametrize(
    "bmi, expected",
    [
        (10, "Underweight"),
        (18.49, "Underweight"),
        (18.5, "Normal"),
        (24.9, "Normal"),
        (24.95, "Normal"),
        (25, "Overweight"),
        (29.9, "Overweight"),
        (30, "Obese"),
        (45, "Obese"),
    ],
)
def test_classification_boundaries(bmi, expected):
    assert classify_bmi(bmi) == expected


@pytest.mark.parametrize("bad", ["abc", "", "   ", "12kg", "1,75"])
def test_non_numeric_input_rejected(bad):
    with pytest.raises(InvalidInputError):
        parse_positive_number(bad, "weight")


@pytest.mark.parametrize("bad", ["-5", "0", "-0.1"])
def test_negative_and_zero_rejected(bad):
    with pytest.raises(InvalidInputError):
        parse_positive_number(bad, "height")


@pytest.mark.parametrize("bad", ["nan", "inf", "-inf"])
def test_nan_and_infinity_rejected(bad):
    with pytest.raises(InvalidInputError):
        parse_positive_number(bad, "weight")


def test_height_in_centimetres_gets_helpful_message():
    with pytest.raises(InvalidInputError, match="metres"):
        validate_weight_height("70", "175")


def test_unrealistic_weight_rejected():
    with pytest.raises(InvalidInputError):
        validate_weight_height("5000", "1.7")


def test_valid_input_returns_floats():
    assert validate_weight_height(" 70 ", "1.75") == (70.0, 1.75)


def test_calculate_bmi_rejects_zero_height():
    with pytest.raises(InvalidInputError):
        calculate_bmi(70, 0)
