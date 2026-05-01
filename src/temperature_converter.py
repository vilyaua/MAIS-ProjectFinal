"""Temperature conversion utilities.

This module provides a single public function, ``convert_temperature``,
for converting values between Celsius, Fahrenheit, and Kelvin with input
validation and physical-range checks.
"""

from __future__ import annotations

from numbers import Real

SUPPORTED_UNITS = {
    "celsius": "Celsius",
    "fahrenheit": "Fahrenheit",
    "kelvin": "Kelvin",
}


def _normalize_unit(unit: str, parameter_name: str) -> str:
    """Return a canonical lowercase unit name after validation."""
    if not isinstance(unit, str):
        raise ValueError(
            f"Invalid {parameter_name} unit: expected one of "
            f"{', '.join(SUPPORTED_UNITS.values())}, got {type(unit).__name__}."
        )

    normalized = unit.strip().lower()
    if normalized not in SUPPORTED_UNITS:
        raise ValueError(
            f"Invalid {parameter_name} unit '{unit}'. Supported units are: "
            f"{', '.join(SUPPORTED_UNITS.values())}."
        )
    return normalized


def _validate_temperature(value: Real) -> float:
    """Validate and return the temperature as a float."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(
            f"Invalid temperature value: expected a numeric value, got "
            f"{type(value).__name__}."
        )

    temperature = float(value)
    if temperature != temperature or temperature in (float("inf"), float("-inf")):
        raise ValueError("Invalid temperature value: expected a finite number.")
    return temperature


def _to_kelvin(value: float, source_unit: str) -> float:
    """Convert a temperature from the source unit to Kelvin."""
    if source_unit == "celsius":
        return value + 273.15
    if source_unit == "fahrenheit":
        return (value - 32.0) * 5.0 / 9.0 + 273.15
    return value


def _from_kelvin(value: float, target_unit: str) -> float:
    """Convert a Kelvin temperature to the target unit."""
    if target_unit == "celsius":
        return value - 273.15
    if target_unit == "fahrenheit":
        return (value - 273.15) * 9.0 / 5.0 + 32.0
    return value


def convert_temperature(
    temperature: Real,
    source_unit: str,
    target_unit: str,
) -> float:
    """Convert a temperature between Celsius, Fahrenheit, and Kelvin.

    Args:
        temperature: Numeric temperature value to convert. ``bool``, NaN,
            and infinity are rejected.
        source_unit: Source unit: Celsius, Fahrenheit, or Kelvin.
        target_unit: Target unit: Celsius, Fahrenheit, or Kelvin.

    Returns:
        The converted temperature value as a float.

    Raises:
        ValueError: If the temperature is not numeric/finite, either unit is
            unsupported, or the input temperature is below absolute zero.
    """
    numeric_temperature = _validate_temperature(temperature)
    normalized_source = _normalize_unit(source_unit, "source")
    normalized_target = _normalize_unit(target_unit, "target")

    kelvin_value = _to_kelvin(numeric_temperature, normalized_source)
    if kelvin_value < 0.0:
        raise ValueError(
            "Invalid temperature value: temperature is below absolute zero."
        )

    return float(_from_kelvin(kelvin_value, normalized_target))
