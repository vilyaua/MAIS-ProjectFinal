import pytest

from src.temperature import convert_temperature


def test_celsius_to_fahrenheit() -> None:
    assert convert_temperature(0, "C", "F") == pytest.approx(32.0)


def test_fahrenheit_to_celsius() -> None:
    assert convert_temperature(32, "F", "C") == pytest.approx(0.0)


def test_kelvin_to_celsius() -> None:
    assert convert_temperature(273.15, "K", "C") == pytest.approx(0.0)


def test_identical_units_return_original_as_float() -> None:
    assert convert_temperature(25, "C", "c") == 25.0


def test_case_insensitive_units() -> None:
    assert convert_temperature(100, "c", "f") == pytest.approx(212.0)


def test_invalid_temperature_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Temperature must be a numeric value"):
        convert_temperature("not-a-number", "C", "F")  # type: ignore[arg-type]


def test_boolean_temperature_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Temperature must be a numeric value"):
        convert_temperature(True, "C", "F")


def test_invalid_unit_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Invalid unit 'X'"):
        convert_temperature(0, "X", "C")


def test_non_string_unit_raises_value_error() -> None:
    with pytest.raises(ValueError, match="source_unit must be one of"):
        convert_temperature(0, 1, "C")  # type: ignore[arg-type]


def test_absolute_zero_allowed() -> None:
    assert convert_temperature(-273.15, "C", "K") == pytest.approx(0.0)
    assert convert_temperature(-459.67, "F", "K") == pytest.approx(0.0)
    assert convert_temperature(0, "K", "C") == pytest.approx(-273.15)


def test_below_absolute_zero_raises_value_error() -> None:
    with pytest.raises(ValueError, match="below absolute zero"):
        convert_temperature(-273.16, "C", "F")
    with pytest.raises(ValueError, match="below absolute zero"):
        convert_temperature(-459.68, "F", "C")
    with pytest.raises(ValueError, match="below absolute zero"):
        convert_temperature(-0.01, "K", "C")
