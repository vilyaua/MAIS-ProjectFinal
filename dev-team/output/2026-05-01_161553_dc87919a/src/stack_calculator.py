from typing import List, Union


class CalculatorError(Exception):
    pass


def precedence(op: str) -> int:
    if op in ("+", "-"):
        return 1
    if op in ("*", "/"):
        return 2
    return 0


def apply_op(op: str, b: Union[int, float], a: Union[int, float]) -> Union[int, float]:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if b == 0:
            raise CalculatorError("Division by zero error")
        return a / b
    raise CalculatorError(f"Unknown operator: {op}")


def is_operator(c: str) -> bool:
    return c in "+-*/"


def tokenize(expression: str) -> List[str]:
    tokens: List[str] = []
    i = 0
    n = len(expression)
    while i < n:
        c = expression[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit():
            num = c
            i += 1
            while i < n and expression[i].isdigit():
                num += expression[i]
                i += 1
            tokens.append(num)
            continue
        elif c in "+-*/()":
            tokens.append(c)
            i += 1
            continue
        else:
            raise CalculatorError(f"Invalid character found: {c}")
    return tokens


def evaluate(expression: str) -> Union[int, float]:
    expression = expression.strip()
    if not expression:
        raise CalculatorError("Empty expression")
    tokens = tokenize(expression)

    values: List[Union[int, float]] = []
    ops: List[str] = []

    def process_operator():
        if not ops or len(values) < 2:
            raise CalculatorError("Invalid syntax: insufficient values for operation")
        op = ops.pop()
        b = values.pop()
        a = values.pop()
        result = apply_op(op, b, a)
        values.append(result)

    i = 0
    n = len(tokens)
    while i < n:
        token = tokens[i]

        if token.isdigit():
            values.append(int(token))
        elif token == "(":  # Push '(' to ops stack
            ops.append(token)
        elif token == ")":  # Solve entire bracket
            while ops and ops[-1] != "(":  # Process until matching '('
                process_operator()
            if not ops:
                raise CalculatorError("Invalid syntax: unmatched parentheses")
            ops.pop()  # Remove the matching '('
        elif is_operator(token):
            while ops and ops[-1] != "(" and precedence(ops[-1]) >= precedence(token):
                process_operator()
            ops.append(token)
        else:
            raise CalculatorError(f"Invalid token found: {token}")
        i += 1

    while ops:
        if ops[-1] == "(" or ops[-1] == ")":
            raise CalculatorError("Invalid syntax: unmatched parentheses")
        process_operator()

    if len(values) != 1:
        raise CalculatorError("Invalid syntax: multiple values left without operators")

    result = values[0]
    # Return int if whole number
    if isinstance(result, float) and result.is_integer():
        return int(result)
    return result


if __name__ == "__main__":
    try:
        expr = input("Enter expression to evaluate: ")
        result = evaluate(expr)
        print("Result:", result)
    except CalculatorError as e:
        print("Error:", e)
    except Exception as e:
        print("Unexpected error:", e)
