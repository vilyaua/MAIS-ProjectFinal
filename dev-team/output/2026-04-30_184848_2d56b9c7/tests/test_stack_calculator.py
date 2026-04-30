import unittest
from src.stack_calculator import evaluate_expression


class TestStackCalculator(unittest.TestCase):

    def test_basic_addition(self):
        self.assertEqual(evaluate_expression("1+2"), 3)

    def test_mixed_operations(self):
        self.assertEqual(evaluate_expression("2 + 3 * 4"), 14)

    def test_parentheses(self):
        self.assertEqual(evaluate_expression("(2 + 3) * 4"), 20)

    def test_nested_parentheses(self):
        self.assertEqual(evaluate_expression("(2 + (3 * 2)) * 4"), 32)

    def test_division(self):
        self.assertAlmostEqual(evaluate_expression("10 / 4"), 2.5)

    def test_division_by_zero(self):
        result = evaluate_expression("5 / 0")
        self.assertTrue(isinstance(result, str) and "division by zero" in result.lower())

    def test_unmatched_parentheses(self):
        result1 = evaluate_expression("(1 + 2"
                                   )
        result2 = evaluate_expression("1 + 2)"
                                   )
        self.assertIn("unmatched parentheses", result1.lower())
        self.assertIn("unmatched parentheses", result2.lower())

    def test_invalid_characters(self):
        result = evaluate_expression("1 + 2 $ 3")
        self.assertIn("invalid character", result.lower())

    def test_malformed_expression(self):
        # Two operators in sequence
        result = evaluate_expression("1 ++ 2")
        self.assertIn("malformed expression", result.lower())

    def test_empty_expression(self):
        result = evaluate_expression("")
        self.assertIn("empty", result.lower())

    def test_multiple_decimal_points(self):
        result = evaluate_expression("1..2 + 3")
        self.assertIn("invalid number format", result.lower())

    def test_float_numbers(self):
        self.assertAlmostEqual(evaluate_expression("3.5 + 2.5"), 6.0)


if __name__ == '__main__':
    unittest.main()
