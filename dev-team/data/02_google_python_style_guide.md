# Google Python Style Guide

## 1. Python Language Rules

### Imports
- Use `import x` for packages and modules
- Use `from x import y` for specific module imports
- Avoid relative imports; use full package names

### Exceptions
- Use built-in exception classes appropriately (e.g., `ValueError` for precondition violations)
- Never use bare `except:` or catch `Exception` unless re-raising
- Minimize code within `try`/`except` blocks
- Use `finally` for cleanup operations

### Mutable Global State
Avoid mutable global state. Module-level constants are permitted using `CAPS_WITH_UNDER`.

### Comprehensions and Generators
Comprehensions are allowed; multiple `for` clauses or filter expressions are not permitted. Optimize for readability.

### Default Argument Values
Avoid mutable objects as defaults. Use `None` and initialize within the function:
```python
def foo(a, b=None):
    if b is None:
        b = []
```

### True/False Evaluations
- Use `if foo:` over explicit comparisons
- Use `if foo is None:` for `None` checks
- For sequences, use `if seq:` rather than `if len(seq):`
- Explicitly compare integers against `0` when appropriate

### Type Annotations
Type-check code at build time with a type checking tool like pytype.

## 2. Python Style Rules

### Line Length
Maximum line length is 80 characters. Use implicit line joining inside parentheses, brackets, and braces.

### Indentation
Use 4 spaces — never tabs.

### Blank Lines
- Two blank lines between top-level definitions
- One blank line between methods

### Comments and Docstrings
Always use three-double-quotes `"""`. Structure as summary line, blank line, then detailed description.

**Functions/Methods:** Document with sections:
- **Args**: List parameters with types and descriptions
- **Returns** (or **Yields**): Describe return value semantics
- **Raises**: List relevant exceptions

### Strings
Use f-strings, `%` operator, or `.format()` method for formatting. Avoid string concatenation with `+` in loops.

**Logging**: Use pattern strings with `%` placeholders, not f-strings.

### Files and Resources
Always explicitly close files and sockets using `with` statements.

### Naming Conventions

| Entity | Public | Internal |
|--------|--------|----------|
| Packages | `lower_with_under` | — |
| Modules | `lower_with_under` | `_lower_with_under` |
| Classes | `CapWords` | `_CapWords` |
| Exceptions | `CapWords` | — |
| Functions | `lower_with_under()` | `_lower_with_under()` |
| Constants | `CAPS_WITH_UNDER` | `_CAPS_WITH_UNDER` |
| Variables | `lower_with_under` | `_lower_with_under` |

### Main
Always use `if __name__ == '__main__':` before executing main logic.

### Function Length
Prefer functions under ~40 lines.

## 3. Type Annotations

- Annotate public APIs and code prone to type errors
- Use `Any` when types shouldn't be expressed
- Use `X | None` for nullable arguments
- Prefer built-in generics (`list[int]`) over typing aliases (`List[int]`)
- Prefer abstract types (`Sequence`) over concrete types (`list`)
