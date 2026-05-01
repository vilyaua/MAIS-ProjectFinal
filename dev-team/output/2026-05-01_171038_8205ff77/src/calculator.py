from typing import List, Union


class CalculatorError(Exception):
    pass


def validate_expression(expr: str) -> None:
    """Validate the expression for allowed characters and balanced parentheses."""
    allowed_chars = set("0123456789+-*/() .\t\n\r")  # Added '.' to allowed characters
    for char in expr:
        if char not in allowed_chars:
            raise CalculatorError(f"Invalid character detected: '{char}'")

    # Check for balanced parentheses
    stack = []
    for char in expr:
        if char == "(":
            stack.append(char)
        elif char == ")":
            if not stack:
                raise CalculatorError("Mismatched parentheses detected.")
            stack.pop()
    if stack:
        raise CalculatorError("Mismatched parentheses detected.")


def precedence(op: str) -> int:
    if op in ("+", "-"):
        return 1
    if op in ("*", "/"):
        return 2
    return 0


def apply_operator(op: str, b: float, a: float) -> float:
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "*":
        return a * b
    elif op == "/":
        if b == 0:
            raise CalculatorError("Division by zero is not allowed.")
        return a / b
    else:
        raise CalculatorError(f"Unknown operator: {op}")


def evaluate_expression(expression: str) -> Union[float, str]:
    """
    Evaluate arithmetic expression using a stack-based approach.

    Args:
        expression (str): The arithmetic expression to evaluate.

    Returns:
        float or str: The numerical result or error message.
    """
    try:
        if not expression or expression.strip() == "":
            raise CalculatorError("Input expression is empty or whitespace.")

        validate_expression(expression)

        # Tokenize expression (support multi-digit and decimal numbers)
        tokens: List[str] = []
        number_buffer = []
        i = 0
        while i < len(expression):
            char = expression[i]
            if char.isdigit() or char == ".":
                number_buffer.append(char)
            else:
                if number_buffer:
                    tokens.append("".join(number_buffer))
                    number_buffer.clear()

                if char in "+-*/()":
                    tokens.append(char)
                elif char.isspace():
                    pass
                else:
                    raise CalculatorError(
                        f"Invalid character detected during tokenization: '{char}'"
                    )
            i += 1

        if number_buffer:
            tokens.append("".join(number_buffer))

        # Edge case: if expression is just a number
        if len(tokens) == 1:
            try:
                return float(tokens[0])
            except ValueError:
                raise CalculatorError("Invalid numeric value.")

        values_stack: List[float] = []
        operators_stack: List[str] = []

        def process_operator():
            if len(values_stack) < 2:
                raise CalculatorError("Syntax error: insufficient values for operator.")
            b = values_stack.pop()
            a = values_stack.pop()
            op = operators_stack.pop()
            result = apply_operator(op, b, a)
            values_stack.append(result)

        idx = 0
        while idx < len(tokens):
            token = tokens[idx]

            if token.isdigit() or _is_float(token):  # number
                values_stack.append(float(token))
            elif token == "(":  # push '(' to operator stack
                operators_stack.append(token)
            elif token == ")":  # until '(' pop and evaluate
                while operators_stack and operators_stack[-1] != "(":  # apply until '('
                    process_operator()
                if not operators_stack or operators_stack[-1] != "(":  # unmatched
                    raise CalculatorError("Mismatched parentheses detected.")
                operators_stack.pop()  # pop '('
            else:  # operator
                while (
                    operators_stack
                    and operators_stack[-1] != "("
                    and precedence(operators_stack[-1]) >= precedence(token)
                ):
                    process_operator()
                operators_stack.append(token)
            idx += 1

        while operators_stack:
            if operators_stack[-1] == "(":  # unmatched
                raise CalculatorError("Mismatched parentheses detected.")
            process_operator()

        if len(values_stack) != 1:
            raise CalculatorError("Syntax error in expression.")

        return values_stack[0]

    except CalculatorError as e:
        return f"Error: {str(e)}"
    except Exception:
        return "Error: An unexpected error occurred during evaluation."


def _is_float(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    expr = input("Enter expression: ")
    result = evaluate_expression(expr)
    print(result)
