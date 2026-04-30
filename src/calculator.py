import re
import logging
from typing import List

# Configure logging
logging.basicConfig(
    filename='calculator.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class CalculatorError(Exception):
    """Base class for calculator exceptions."""
    pass


class ValidationError(CalculatorError):
    """Raised when an expression contains invalid characters or malformed syntax."""
    pass


class ParenthesesMismatchError(CalculatorError):
    """Raised when parentheses in the expression are mismatched."""
    pass


class DivisionByZeroError(CalculatorError):
    """Raised when division by zero is attempted."""
    pass


class Calculator:
    OPERATORS = {'+': 1, '-': 1, '*': 2, '/': 2}
    VALID_TOKENS_RE = re.compile(r'^[0-9+\-*/().\s]+$')

    def __init__(self) -> None:
        pass

    @staticmethod
    def sanitize_expression(expression: str) -> str:
        """Sanitize the input expression to prevent unsafe operations.

        This implementation ensures that the expression contains only digits, 
        whitespace, and valid operators including parentheses.

        Args:
            expression: A string containing the arithmetic expression.

        Returns:
            The sanitized expression string without leading/trailing whitespace.

        Raises:
            ValidationError: If invalid characters are found in the expression.
        """
        expression = expression.strip()

        if not expression:
            raise ValidationError("Empty expression is not allowed.")

        if not Calculator.VALID_TOKENS_RE.match(expression):
            raise ValidationError(
                "Expression contains invalid characters. "
                "Only digits, whitespace, +, -, *, /, and parentheses are allowed.")

        # Additional sanitization can be implemented here if needed

        return expression

    @staticmethod
    def tokenize(expression: str) -> List[str]:
        """Tokenize the expression into numbers, operators, and parentheses.

        Args:
            expression: The sanitized string expression.

        Returns:
            A list of tokens as strings.
        """
        tokens = []
        number_buffer = []

        for char in expression:
            if char.isdigit() or char == '.':
                number_buffer.append(char)
            else:
                if number_buffer:
                    tokens.append(''.join(number_buffer))
                    number_buffer = []

                if char in Calculator.OPERATORS or char in '()':
                    tokens.append(char)
                elif char.isspace():
                    continue
                else:
                    # Should not reach here due to prior validation
                    raise ValidationError(f"Invalid character encountered during tokenizing: {char}")

        if number_buffer:
            tokens.append(''.join(number_buffer))

        return tokens

    @staticmethod
    def precedence(op: str) -> int:
        """Return the precedence of the given operator."""
        return Calculator.OPERATORS.get(op, 0)

    @staticmethod
    def apply_operator(operators: List[str], values: List[float]) -> None:
        """Apply operator on the top of the operators stack to the top two values in the values stack."""
        operator = operators.pop()

        right = values.pop()
        left = values.pop()

        if operator == '+':
            values.append(left + right)

        elif operator == '-':
            values.append(left - right)

        elif operator == '*':
            values.append(left * right)

        elif operator == '/':
            if right == 0:
                raise DivisionByZeroError("Division by zero is not allowed.")
            values.append(left / right)

    @staticmethod
    def evaluate(expression: str) -> float:
        """Validate, parse, and evaluate the arithmetic expression.

        Args:
            expression: A string representing an arithmetic expression.

        Returns:
            The numeric result as a float.

        Raises:
            ValidationError: For invalid characters or malformed expressions.
            ParenthesesMismatchError: For unmatched parentheses.
            DivisionByZeroError: For division by zero attempts.
        """
        try:
            expr = Calculator.sanitize_expression(expression)
            tokens = Calculator.tokenize(expr)

            values: List[float] = []
            operators: List[str] = []

            # Stack based evaluation with precedence and parentheses handling
            for token in tokens:
                if re.match(r'\d+(\.\d+)?', token):  # Number
                    values.append(float(token))

                elif token == '(':  # Left parenthesis
                    operators.append(token)

                elif token == ')':  # Right parenthesis
                    while operators and operators[-1] != '(':  # Pop till matching '('
                        Calculator.apply_operator(operators, values)

                    if not operators:
                        raise ParenthesesMismatchError("Unmatched parentheses detected.")
                    operators.pop()  # Remove '('

                else:  # Operator
                    while (operators and operators[-1] != '(' and
                           Calculator.precedence(operators[-1]) >= Calculator.precedence(token)):
                        Calculator.apply_operator(operators, values)
                    operators.append(token)

            while operators:
                if operators[-1] == '(':  # Unmatched left parenthesis
                    raise ParenthesesMismatchError("Unmatched parentheses detected.")
                Calculator.apply_operator(operators, values)

            if len(values) != 1:
                raise ValidationError("Malformed expression.")

            return values[0]

        except CalculatorError:
            # Re-raise known calculator exceptions
            raise

        except Exception as ex:
            # Log unexpected exceptions
            logging.error(f"Unexpected error during evaluation: {ex}", exc_info=True)
            raise ValidationError("Error evaluating the expression.") from ex
