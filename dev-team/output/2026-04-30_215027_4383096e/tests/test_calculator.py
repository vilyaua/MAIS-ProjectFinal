import pytest
from src.calculator import (
    Calculator, ValidationError, ParenthesesMismatchError, DivisionByZeroError
)


def test_basic_operations():
    assert Calculator.evaluate('1 + 2') == 3
    assert Calculator.evaluate('5 - 3') == 2
    assert Calculator.evaluate('4 * 3') == 12
    assert Calculator.evaluate('10 / 2') == 5


def test_operator_precedence():
    assert Calculator.evaluate('2 + 3 * 4') == 14
    assert Calculator.evaluate('(2 + 3) * 4') == 20


def test_nested_parentheses():
    expr = '(1 + (2 + 3) * (4 - 2)) / 2'
    assert Calculator.evaluate(expr) == 5


def test_invalid_characters():
    with pytest.raises(ValidationError):
        Calculator.evaluate('2 + 3a')


def test_unmatched_parentheses():
    with pytest.raises(ParenthesesMismatchError):
        Calculator.evaluate('(2 + 3')
    with pytest.raises(ParenthesesMismatchError):
        Calculator.evaluate('2 + 3)')


def test_division_by_zero():
    with pytest.raises(DivisionByZeroError):
        Calculator.evaluate('5 / 0')


def test_empty_expression():
    with pytest.raises(ValidationError):
        Calculator.evaluate('')


def test_malformed_expression():
    # Testing expression that becomes malformed due to missing operand
    with pytest.raises(ValidationError):
        Calculator.evaluate('2 + * 3')


def test_float_numbers():
    assert Calculator.evaluate('3.5 + 2.1') == pytest.approx(5.6)
    assert Calculator.evaluate('(1.1 + 1.9) * 2') == pytest.approx(6.0)


def test_whitespace_handling():
    assert Calculator.evaluate(' 3 +    4 ') == 7
    assert Calculator.evaluate('\t(1+1)\n') == 2
