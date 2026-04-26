# Python Error Handling Best Practices

## Exception Hierarchy
```
BaseException
├── SystemExit
├── KeyboardInterrupt
├── GeneratorExit
└── Exception
    ├── ValueError
    ├── TypeError
    ├── KeyError
    ├── IndexError
    ├── AttributeError
    ├── FileNotFoundError
    ├── IOError
    ├── RuntimeError
    ├── StopIteration
    └── ... (many more)
```

## Basic Try/Except
```python
try:
    result = int(user_input)
except ValueError:
    print("Invalid number")
except (TypeError, KeyError) as e:
    print(f"Error: {e}")
else:
    print(f"Success: {result}")  # Runs only if no exception
finally:
    print("Always runs")  # Cleanup code
```

## Catching Specific Exceptions
```python
# BAD — catches everything, hides bugs
try:
    do_something()
except:
    pass

# BAD — too broad
try:
    do_something()
except Exception:
    pass

# GOOD — specific
try:
    value = my_dict[key]
except KeyError:
    value = default
```

## Custom Exceptions
```python
class AppError(Exception):
    """Base exception for the application."""

class ValidationError(AppError):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class NotFoundError(AppError):
    def __init__(self, resource: str, id: str):
        self.resource = resource
        self.id = id
        super().__init__(f"{resource} '{id}' not found")

# Usage
raise ValidationError("email", "invalid format")
raise NotFoundError("User", "123")
```

## Exception Chaining
```python
try:
    result = parse_config(path)
except FileNotFoundError as e:
    raise ConfigError(f"Config missing: {path}") from e

# Suppress original exception
try:
    result = parse_config(path)
except FileNotFoundError:
    raise ConfigError("Using defaults") from None
```

## Context Managers for Resource Safety
```python
# Files
with open('data.txt') as f:
    content = f.read()

# Locks
import threading
lock = threading.Lock()
with lock:
    shared_resource.modify()

# Database connections
with db.connect() as conn:
    conn.execute(query)
```

## LBYL vs EAFP

### LBYL (Look Before You Leap)
```python
if key in my_dict:
    value = my_dict[key]
else:
    value = default
```

### EAFP (Easier to Ask Forgiveness than Permission) — Pythonic
```python
try:
    value = my_dict[key]
except KeyError:
    value = default
```

## Logging Exceptions
```python
import logging

logger = logging.getLogger(__name__)

try:
    risky_operation()
except Exception:
    logger.exception("Operation failed")  # Includes traceback
    raise  # Re-raise after logging
```

## Assertions
```python
# Use for debugging, not for input validation
assert isinstance(data, list), "Expected a list"
assert len(data) > 0, "Data cannot be empty"

# DON'T use for user input — can be disabled with python -O
# BAD:
assert user_input.isdigit(), "Must be a number"
# GOOD:
if not user_input.isdigit():
    raise ValueError("Must be a number")
```

## Exception Groups (Python 3.11+)
```python
# Raise multiple exceptions at once
errors = []
for item in items:
    try:
        process(item)
    except ValueError as e:
        errors.append(e)

if errors:
    raise ExceptionGroup("Processing failed", errors)

# Catch with except*
try:
    process_all()
except* ValueError as eg:
    for e in eg.exceptions:
        print(f"ValueError: {e}")
except* TypeError as eg:
    for e in eg.exceptions:
        print(f"TypeError: {e}")
```

## Best Practices Summary

1. **Be specific** — catch the narrowest exception possible
2. **Don't silently swallow** — at minimum, log the exception
3. **Use `finally`** or context managers for cleanup
4. **Create custom exceptions** for your application's error domain
5. **Chain exceptions** with `from` to preserve context
6. **Re-raise** with bare `raise` to preserve the traceback
7. **Keep try blocks small** — only wrap the code that might fail
8. **Document exceptions** in docstrings with `Raises:` section
9. **Use EAFP** over LBYL for Pythonic code
10. **Never use assertions** for input validation
