from typing import List, Tuple, Union


class CalculatorError(Exception):
    pass


def tokenize(expression: str) -> List[str]:
    """
    Tokenize the input expression into numbers, operators, and parentheses.
    Spaces are ignored.

    Raises CalculatorError for invalid characters.
    """
    tokens = []
    i = 0
    length = len(expression)

    while i < length:
        c = expression[i]
        if c.isspace():
            i += 1
            continue
        elif c.isdigit() or c == '.':
            # Parse a number (integer or float)
            num_start = i
            dot_count = 0
            while i < length and (expression[i].isdigit() or expression[i] == '.'):
                if expression[i] == '.':
                    dot_count += 1
                    if dot_count > 1:
                        raise CalculatorError("Invalid number format with multiple decimals")
                i += 1
            tokens.append(expression[num_start:i])
            continue
        elif c in '+-*/()':
            tokens.append(c)
            i += 1
        else:
            raise CalculatorError(f"Invalid character found: '{c}'")
    return tokens


def precedence(op: str) -> int:
    if op in ('+', '-'):
        return 1
    if op in ('*', '/'):
        return 2
    return 0


def apply_operator(operators: List[str], operands: List[float]) -> None:
    if len(operands) < 2:
        raise CalculatorError("Malformed expression: insufficient operands")
    right = operands.pop()
    left = operands.pop()
    op = operators.pop()

    if op == '+':
        operands.append(left + right)
    elif op == '-':
        operands.append(left - right)
    elif op == '*':
        operands.append(left * right)
    elif op == '/':
        if right == 0:
            raise CalculatorError("Division by zero")
        operands.append(left / right)
    else:
        raise CalculatorError(f"Unknown operator: {op}")


def evaluate_expression(expression: str) -> Union[float, str]:
    """
    Evaluate the arithmetic expression using stacks.
    Returns the result as float or an error message string.
    """
    if not expression or expression.strip() == '':
        return "Error: Input expression is empty or invalid"

    try:
        tokens = tokenize(expression)
    except CalculatorError as e:
        return f"Error: {str(e)}"

    operators: List[str] = []
    operands: List[float] = []

    # This helper will process operators until the condition is false
    def process_until(condition):
        while operators and condition(operators[-1]):
            apply_operator(operators, operands)

    try:
        i = 0
        n = len(tokens)

        while i < n:
            token = tokens[i]

            if token.isdigit() or (token.count('.') == 1 and token.replace('.', '').isdigit()):
                # Number token
                operands.append(float(token))
            elif token == '(':  # Push '(' operator
                operators.append(token)
            elif token == ')':  # Solve entire bracket
                while operators and operators[-1] != '(':  # apply until '(' found
                    apply_operator(operators, operands)
                if not operators or operators[-1] != '(':  # no matching parenthesis
                    return "Error: Unmatched parentheses"
                operators.pop()  # pop the '('
            elif token in '+-*/':
                # process higher or equal precedence ops before pushing new
                process_until(lambda op: op != '(' and precedence(op) >= precedence(token))
                operators.append(token)
            else:
                return f"Error: Invalid token '{token}'"
            i += 1

        # apply remaining ops
        process_until(lambda op: op != '(')
        if operators:
            if '(' in operators:
                return "Error: Unmatched parentheses"
            else:
                return "Error: Malformed expression"

        if len(operands) != 1:
            return "Error: Malformed expression"
        return operands[0]
    except CalculatorError as e:
        return f"Error: {str(e)}"


if __name__ == '__main__':
    # Basic manual tests
    exp = input("Enter expression: ")
    result = evaluate_expression(exp)
    print(f"Result: {result}")
