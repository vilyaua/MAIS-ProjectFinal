from typing import Union


def convert_temperature(
    temperature: Union[float, int], source_unit: str, target_unit: str
) -> float:
    """
    Convert temperature between Celsius, Fahrenheit, and Kelvin.

    Args:
        temperature (float or int): The temperature value to convert.
        source_unit (str): The unit of the input temperature ('C', 'F', 'K').
        target_unit (str): The unit to convert the temperature to ('C', 'F', 'K').

    Returns:
        float: The converted temperature rounded to two decimals.

    Raises:
        ValueError: If the temperature is below 0 K or units are invalid.
    """
    # Normalize unit strings to uppercase
    source_unit = source_unit.upper()
    target_unit = target_unit.upper()

    valid_units = {'C', 'F', 'K'}

    # Validate source and target units
    if source_unit not in valid_units:
        raise ValueError(f"Invalid source unit '{source_unit}'. Must be one of {valid_units}.")
    if target_unit not in valid_units:
        raise ValueError(f"Invalid target unit '{target_unit}'. Must be one of {valid_units}.")

    # Validate temperature numeric
    if not isinstance(temperature, (float, int)):
        raise ValueError("Temperature must be a numeric value (float or int).")

    # Check valid Kelvin temperature limit
    # Convert input temperature to Kelvin for validation
    if source_unit == 'C':
        kelvin_temp = temperature + 273.15
    elif source_unit == 'F':
        kelvin_temp = (temperature - 32) * 5 / 9 + 273.15
    else:  # source_unit == 'K'
        kelvin_temp = temperature

    if kelvin_temp < 0:
        raise ValueError("Temperature below absolute zero (0 K) is physically invalid.")

    # If same source and target unit, return rounded original temperature
    if source_unit == target_unit:
        return round(float(temperature), 2)

    # Conversion formulas
    def c_to_f(c: float) -> float:
        return c * 9 / 5 + 32

    def f_to_c(f: float) -> float:
        return (f - 32) * 5 / 9

    def c_to_k(c: float) -> float:
        return c + 273.15

    def k_to_c(k: float) -> float:
        return k - 273.15

    # Convert source to Celsius as an intermediate step
    if source_unit == 'C':
        celsius = float(temperature)
    elif source_unit == 'F':
        celsius = f_to_c(float(temperature))
    else:  # 'K'
        celsius = k_to_c(float(temperature))

    # Convert Celsius to target
    if target_unit == 'C':
        result = celsius
    elif target_unit == 'F':
        result = c_to_f(celsius)
    else:  # 'K'
        result = c_to_k(celsius)

    return round(result, 2)
