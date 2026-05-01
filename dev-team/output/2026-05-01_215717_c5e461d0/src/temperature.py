"""Temperature conversion utilities."""

from __future__ import annotations


ABSOLUTE_ZERO_C = -273.15
ABSOLUTE_ZERO_F = -459.67
ABSOLUTE_ZERO_K = 0.0
ALLOWED_UNITS = {"C", "F", "K"}


def convert_temperature(
    temperature: int | float,
    source_unit: str,
    target_unit: str,
) -> float:
    """Convert a temperature between Celsius, Fahrenheit, and Kelvin.

    Args:
        temperature: Numeric temperature value to convert.
        source_unit: Current unit: 'C', 'F', or 'K' (case-insensitive).
        target_unit: Target unit: 'C', 'F', or 'K' (case-insensitive).

    Returns:
        Converted temperature as a float. If source and target units match,
        the original numeric value is returned as a float.

    Raises:
        ValueError: If temperature is not numeric, units are invalid, or the
            temperature is below absolute zero for its source unit.
    """
    value = _validate_temperature(temperature)
    source = _validate_unit(source_unit, "source_unit")
    target = _validate_unit(target_unit, "target_unit")
    _validate_absolute_zero(value, source)

    if source == target:
        return value

    celsius = _to_celsius(value, source)
    return _from_celsius(celsius, target)


def _validate_temperature(temperature: int | float) -> float:
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
        raise ValueError("Temperature must be a numeric value (int or float).")
    return float(temperature)


def _validate_unit(unit: str, parameter_name: str) -> str:
    if not isinstance(unit, str):
        raise ValueError(
            f"{parameter_name} must be one of 'C', 'F', or 'K' (case-insensitive)."
        )

    normalized = unit.strip().upper()
    if normalized not in ALLOWED_UNITS:
        raise ValueError(
            f"Invalid unit '{unit}'. Unit must be one of 'C', 'F', or 'K' "
            "(case-insensitive)."
        )
    return normalized


def _validate_absolute_zero(value: float, unit: str) -> None:
    minimums = {
        "C": ABSOLUTE_ZERO_C,
        "F": ABSOLUTE_ZERO_F,
        "K": ABSOLUTE_ZERO_K,
    }
    minimum = minimums[unit]
    if value < minimum:
        raise ValueError(
            f"Temperature {value} {unit} is below absolute zero ({minimum} {unit})."
        )


def _to_celsius(value: float, unit: str) -> float:
    if unit == "C":
        return value
    if unit == "F":
        return (value - 32.0) * 5.0 / 9.0
    return value - 273.15


def _from_celsius(value: float, unit: str) -> float:
    if unit == "C":
        return value
    if unit == "F":
        return (value * 9.0 / 5.0) + 32.0
    return value + 273.15
