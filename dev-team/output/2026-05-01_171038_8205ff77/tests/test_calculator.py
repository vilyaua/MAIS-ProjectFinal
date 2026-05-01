import pytest
from src.calculator import evaluate_expression


def test_basic_operations():
    assert evaluate_expression("1 + 2") == 3.0
    assert evaluate_expression("3 - 2") == 1.0
    assert evaluate_expression("2 * 3") == 6.0
    assert evaluate_expression("8 / 4") == 2.0


def test_operator_precedence():
    assert evaluate_expression("2 + 3 * 4") == 14.0
    assert evaluate_expression("(2 + 3) * 4") == 20.0


def test_with_whitespace():
    assert evaluate_expression("  7  + 8 ") == 15.0


def test_mismatched_parentheses():
    assert "Error: Mismatched parentheses detected." in evaluate_expression("(1 + 2")
    assert "Error: Mismatched parentheses detected." in evaluate_expression("1 + 2)")


def test_invalid_characters():
    assert "Error: Invalid character detected" in evaluate_expression("1 + 2a")
    assert "Error" in evaluate_expression("import os")


def test_division_by_zero():
    assert "Error: Division by zero is not allowed." in evaluate_expression("4 / 0")


def test_empty_input():
    assert "Error: Input expression is empty or whitespace." in evaluate_expression("")
    assert "Error: Input expression is empty or whitespace." in evaluate_expression("   ")


def test_single_number():
    assert evaluate_expression("42") == 42.0
    assert evaluate_expression("3.1415") == 3.1415


def test_syntax_errors():
    # Cases that should cause syntax errors
    assert "Error" in evaluate_expression("+")
    assert "Error" in evaluate_expression("1 +")
    assert "Error" in evaluate_expression("* 5")
    assert "Error" in evaluate_expression("(1 + 2))")
    assert "Error" in evaluate_expression("(()")


if __name__ == "__main__":
    pytest.main(["-v"])
