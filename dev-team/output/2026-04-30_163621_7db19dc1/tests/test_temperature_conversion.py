import pytest
from src.temperature_conversion import convert_temperature

# Test correct conversions
@pytest.mark.parametrize("temp,src,tar,expected", [
    (0, 'C', 'F', 32.00),
    (100, 'C', 'F', 212.00),
    (32, 'F', 'C', 0.00),
    (212, 'F', 'C', 100.00),
    (0, 'C', 'K', 273.15),
    (273.15, 'K', 'C', 0.00),
    (32, 'F', 'K', 273.15),
    (212, 'F', 'K', 373.15),
    (0, 'K', 'F', -459.67),
    (273.15, 'K', 'F', 32.00),
    (25.0, 'C', 'C', 25.00),
    (-40, 'C', 'F', -40.00),
    (-40, 'F', 'C', -40.00),
    (0, 'K', 'K', 0.00),
])
def test_valid_conversions(temp, src, tar, expected):
    result = convert_temperature(temp, src, tar)
    assert result == expected

# Test invalid temperature below 0 Kelvin
@pytest.mark.parametrize("temp,src,tar", [
    (-1, 'K', 'C'),
    (-274, 'C', 'F'),
    (-500, 'F', 'K'),
])
def test_invalid_temperature_below_absolute_zero(temp, src, tar):
    with pytest.raises(ValueError) as excinfo:
        convert_temperature(temp, src, tar)
    assert "below absolute zero" in str(excinfo.value)

# Test invalid units
@pytest.mark.parametrize("temp,src,tar", [
    (100, 'X', 'C'),
    (100, 'C', 'Y'),
    (100, '', 'F'),
    (100, 'C', ''),
])
def test_invalid_units(temp, src, tar):
    with pytest.raises(ValueError) as excinfo:
        convert_temperature(temp, src, tar)
    assert "Invalid source unit" in str(excinfo.value) or "Invalid target unit" in str(excinfo.value)

# Test non-numeric temperature
def test_non_numeric_temperature():
    with pytest.raises(ValueError) as excinfo:
        convert_temperature('abc', 'C', 'F')
    assert "Temperature must be a numeric value" in str(excinfo.value)
