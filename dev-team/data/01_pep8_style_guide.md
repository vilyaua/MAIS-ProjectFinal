# PEP 8 – Style Guide for Python Code

## Introduction

PEP 8 establishes coding conventions for Python's standard library. The document emphasizes that "code is read much more often than it is written," making readability the paramount concern.

## Code Layout

### Indentation
Use 4 spaces per indentation level. Continuation lines should align wrapped elements either vertically using implicit line joining or through hanging indents.

### Tabs or Spaces
Spaces are the preferred indentation method. Python prohibits mixing tabs and spaces.

### Maximum Line Length
Limit all lines to 79 characters maximum. Docstrings and comments should be limited to 72 characters. For teams that prefer longer lines, up to 99 characters is acceptable.

### Binary Operator Line Breaks
Modern convention breaks lines *before* binary operators rather than after.

### Blank Lines
- Surround top-level function and class definitions with two blank lines
- Separate methods within a class with one blank line
- Use blank lines sparingly within functions to indicate logical sections

### Source File Encoding
Core Python code should use UTF-8 without encoding declarations.

### Imports
- Place imports on separate lines
- Position imports at the file top, after module comments and docstrings
- Group imports in this order:
  1. Standard library
  2. Related third-party packages
  3. Local application/library imports
- Separate each group with a blank line
- Prefer absolute imports over relative imports
- Avoid wildcard imports (`from module import *`)

## String Quotes
Single and double quotes are equivalent; choose one convention and apply it consistently. For triple-quoted strings, always use double quotes.

## Whitespace in Expressions and Statements

### Avoid extraneous whitespace:
- Inside parentheses, brackets, or braces: use `spam(ham[1], {eggs: 2})`
- Between trailing commas and closing delimiters: use `foo = (0,)`
- Before commas, semicolons, or colons: use `if x == 4: print(x, y)`

### Recommendations:
- Always surround binary assignment operators with single spaces
- Surround comparison operators with spaces
- Don't use spaces around `=` for keyword arguments or defaults

## Comments

Comments contradicting code are harmful. Maintain comment accuracy when code changes.

### Block Comments
Each line starts with `#` and a space. Separate paragraphs with a line containing only `#`.

### Inline Comments
Use sparingly, separated from statements by at least two spaces.

### Documentation Strings
Write docstrings for all public modules, functions, classes, and methods.

## Naming Conventions

### Styles:
- `lowercase` / `lower_case_with_underscores` — modules, functions, variables
- `UPPERCASE` / `UPPER_CASE_WITH_UNDERSCORES` — constants
- `CapitalizedWords` (CamelCase) — classes
- `_single_leading_underscore` — weak internal use indicator
- `__double_leading_underscore` — invokes name mangling
- `__double_leading_and_trailing__` — reserved magic methods

### Names to Avoid:
Never use 'l', 'O', or 'I' as single-character names.

### Specific Conventions:
- Modules: short, lowercase names
- Classes: CapWords convention
- Exceptions: CapWords + "Error" suffix
- Functions/Variables: lowercase_with_underscores
- Constants: UPPER_CASE_WITH_UNDERSCORES
- Use `self` for instance methods, `cls` for class methods

## Programming Recommendations

- Use `is` / `is not` for singleton comparisons (like `None`)
- Use `isinstance()` rather than direct type comparison
- For sequences, use truthiness: `if seq:` not `if len(seq):`
- Use `startswith()` and `endswith()` instead of string slicing
- Don't compare booleans to `True` or `False`
- Use `def` instead of lambda assignment
- Derive exceptions from `Exception` rather than `BaseException`
- Catch specific exceptions instead of bare `except:`
- Limit `try` blocks to the minimum necessary code
- Use `with` statements for resource management
- Be consistent with return statements

## Type Annotations

- Use a single space after colons in annotations
- Use spaces around `->` arrows
- Don't use spaces around `=` for unannotated defaults
- Use spaces when combining annotations with defaults: `def f(x: int = 0):`
