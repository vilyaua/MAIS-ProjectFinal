# Python typing Module

## Overview
The `typing` module provides runtime support for type hints. Python doesn't enforce type annotations at runtime — they're used by static type checkers, IDEs, and linters.

## Type Aliases

```python
# Python 3.12+ using type statement
type Vector = list[float]

# Backwards compatible
from typing import TypeAlias
Vector: TypeAlias = list[float]
```

## NewType - Distinct Types
```python
from typing import NewType

UserId = NewType('UserId', int)
some_id = UserId(524313)

def get_user_name(user_id: UserId) -> str: ...
```

## Basic Types

### Optional & Union
```python
from typing import Optional, Union

def foo(arg: Optional[int] = None) -> None: ...  # Same as int | None
def bar(value: int | str) -> None: ...  # Modern syntax
```

### Literal
```python
from typing import Literal

type Mode = Literal['r', 'rb', 'w', 'wb']
def open_helper(file: str, mode: Mode) -> str: ...
```

## Generic Types
```python
from typing import TypeVar

T = TypeVar('T')

def first[T](l: Sequence[T]) -> T:
    return l[0]
```

### User-Defined Generic Classes
```python
class LoggedVar[T]:
    def __init__(self, value: T, name: str) -> None:
        self.value = value
        self.name = name

    def set(self, new: T) -> None:
        self.value = new

    def get(self) -> T:
        return self.value
```

### Tuples
```python
x: tuple[int, str] = (5, "foo")       # Fixed-length
y: tuple[int, ...] = (1, 2, 3)        # Variable-length
```

## Callable Types
```python
from collections.abc import Callable

def feeder(get_next_item: Callable[[], str]) -> None: ...
def async_query(on_success: Callable[[int], None]) -> None: ...
```

## Special Forms

### ClassVar
```python
from typing import ClassVar

class Starship:
    stats: ClassVar[dict[str, int]] = {}  # class variable
    damage: int = 10                       # instance variable
```

### Final
```python
from typing import Final
MAX_SIZE: Final = 9000
```

### Annotated
```python
from typing import Annotated
T1 = Annotated[int, "positive"]
```

## TypedDict
```python
from typing import TypedDict, Required, NotRequired

class Person(TypedDict):
    name: str
    age: int
    email: NotRequired[str]  # optional key
```

## Protocol - Structural Subtyping
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Closable(Protocol):
    def close(self) -> None: ...

class MyFile:
    def close(self) -> None: ...

def close_all(things: list[Closable]) -> None:
    for thing in things:
        thing.close()
```

## Any vs object
- `Any`: Bypass type checking entirely
- `object`: Typesafe base type (restrictive)
