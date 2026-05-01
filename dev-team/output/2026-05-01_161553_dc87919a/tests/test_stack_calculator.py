import pytest
from src.stack_calculator import CalculatorError, evaluate


def test_basic_arithmetic():
    assert evaluate("1 + 1") == 2
    assert evaluate("2 - 5") == -3
    assert evaluate("3 * 4") == 12
    assert evaluate("12 / 4") == 3


def test_operator_precedence():
    assert evaluate("2 + 3 * 4") == 14
    assert evaluate("(2 + 3) * 4") == 20
    assert evaluate("2 * (3 + 4)") == 14
    assert evaluate("10 / (5 - 3)") == 5


def test_whitespace():
    assert evaluate(" 2 + 3 ") == 5
    assert evaluate(" ( 1 + 2 ) * 3 ") == 9


def test_unmatched_parentheses():
    with pytest.raises(CalculatorError) as err:
        evaluate("(1 + 2")
    assert "unmatched parentheses" in str(err.value).lower()

    with pytest.raises(CalculatorError) as err:
        evaluate("1 + 2)")
    assert "unmatched parentheses" in str(err.value).lower()


def test_division_by_zero():
    with pytest.raises(CalculatorError) as err:
        evaluate("5 / 0")
    assert "division by zero" in str(err.value).lower()


def test_invalid_characters():
    with pytest.raises(CalculatorError) as err:
        evaluate("3 + x")
    assert "invalid character" in str(err.value).lower()


def test_empty_expression():
    with pytest.raises(CalculatorError) as err:
        evaluate("")
    assert "empty expression" in str(err.value).lower()


def test_float_results():
    assert evaluate("3 / 2") == 1.5
    assert evaluate("10 / 4") == 2.5


def test_complex_expression():
    assert evaluate("3 + 4 * 2 / (1 - 5)") == 1.0
    assert evaluate("(1+(4+5+2)-3)+(6+8)") == 23
