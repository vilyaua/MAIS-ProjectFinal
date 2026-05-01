"""Tests for temperature conversion utilities."""

from __future__ import annotations

import math

import pytest

from src.temperature_converter import convert_temperature


@pytest.mark.parametrize(
    ("temperature", "source", "target", "expected"),
    [
        (0, "Celsius", "Fahrenheit", 32.0),
        (100, "Celsius", "Fahrenheit", 212.0),
        (0, "Celsius", "Kelvin", 273.15),
        (273.15, "Kelvin", "Celsius", 0.0),
        (32, "Fahrenheit", "Celsius", 0.0),
        (212, "Fahrenheit", "Celsius", 100.0),
        (32, "Fahrenheit", "Kelvin", 273.15),
        (373.15, "Kelvin", "Fahrenheit", 212.0),
        (10, "Celsius", "Celsius", 10.0),
        (50, "Fahrenheit", "Fahrenheit", 50.0),
        (300, "Kelvin", "Kelvin", 300.0),
    ],
)
def test_convert_temperature_valid_pairs(
    temperature: float,
    source: str,
    target: str,
    expected: float,
) -> None:
    result = convert_temperature(temperature, source, target)

    assert isinstance(result, float)
    assert result == pytest.approx(expected)


def test_units_are_case_insensitive_and_trimmed() -> None:
    assert convert_temperature(0, " cElSiUs ", " kELvin ") == pytest.approx(273.15)


@pytest.mark.parametrize(
    ("source", "target", "message"),
    [
        ("Rankine", "Celsius", "Invalid source unit"),
        ("Celsius", "Rankine", "Invalid target unit"),
        (123, "Kelvin", "Invalid source unit"),
    ],
)
def test_invalid_units_raise_descriptive_exception(
    source: object,
    target: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        convert_temperature(10, source, target)  # type: ignore[arg-type]


@pytest.mark.parametrize("temperature", ["hot", None, object(), True])
def test_non_numeric_temperature_raises_descriptive_exception(
    temperature: object,
) -> None:
    with pytest.raises(ValueError, match="Invalid temperature value"):
        convert_temperature(temperature, "Celsius", "Kelvin")  # type: ignore[arg-type]


@pytest.mark.parametrize("temperature", [math.nan, math.inf, -math.inf])
def test_non_finite_temperature_raises_descriptive_exception(
    temperature: float,
) -> None:
    with pytest.raises(ValueError, match="finite number"):
        convert_temperature(temperature, "Celsius", "Kelvin")


@pytest.mark.parametrize(
    ("temperature", "unit"),
    [
        (-0.01, "Kelvin"),
        (-273.16, "Celsius"),
        (-459.68, "Fahrenheit"),
    ],
)
def test_temperatures_below_absolute_zero_raise_exception(
    temperature: float,
    unit: str,
) -> None:
    with pytest.raises(ValueError, match="below absolute zero"):
        convert_temperature(temperature, unit, "Kelvin")


def test_extremely_high_temperature_within_physical_range() -> None:
    assert convert_temperature(1_000_000, "Celsius", "Kelvin") == pytest.approx(
        1_000_273.15
    )


def test_absolute_zero_boundary_is_allowed() -> None:
    assert convert_temperature(0, "Kelvin", "Celsius") == pytest.approx(-273.15)
    assert convert_temperature(-273.15, "Celsius", "Kelvin") == pytest.approx(0.0)
    assert convert_temperature(-459.67, "Fahrenheit", "Kelvin") == pytest.approx(0.0)
