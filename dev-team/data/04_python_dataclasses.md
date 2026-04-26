# Python dataclasses Module

## Basic Usage
```python
from dataclasses import dataclass

@dataclass
class InventoryItem:
    name: str
    unit_price: float
    quantity_on_hand: int = 0

    def total_cost(self) -> float:
        return self.unit_price * self.quantity_on_hand
```

This automatically generates `__init__()`, `__repr__()`, and `__eq__()`.

## Decorator Parameters
```python
@dataclass(
    init=True,        # Generate __init__
    repr=True,        # Generate __repr__
    eq=True,          # Generate __eq__
    order=False,      # Generate ordering methods
    frozen=False,     # Make instances immutable
    kw_only=False,    # All fields keyword-only
    slots=False,      # Generate __slots__
)
```

## field() Function
```python
from dataclasses import dataclass, field

@dataclass
class C:
    mylist: list[int] = field(default_factory=list)
```

Parameters: `default`, `default_factory`, `init`, `repr`, `hash`, `compare`, `metadata`, `kw_only`.

## Frozen Instances
```python
@dataclass(frozen=True)
class FrozenPoint:
    x: float
    y: float

p = FrozenPoint(1.0, 2.0)
p.x = 3.0  # Raises FrozenInstanceError
```

## Slots (Python 3.10+)
```python
@dataclass(slots=True)
class Point:
    x: float
    y: float
# Reduced memory, faster attribute access
```

## Post-init Processing
```python
@dataclass
class C:
    a: float
    b: float
    c: float = field(init=False)

    def __post_init__(self):
        self.c = self.a + self.b
```

## InitVar for init-only parameters
```python
from dataclasses import InitVar

@dataclass
class C:
    i: int
    database: InitVar[DatabaseType | None] = None

    def __post_init__(self, database):
        if database is not None:
            self.i = database.lookup('i')
```

## Keyword-only Fields
```python
from dataclasses import KW_ONLY

@dataclass
class Point:
    x: float
    _: KW_ONLY
    y: float
    z: float

p = Point(0, y=1.5, z=2.0)
```

## Utility Functions
```python
from dataclasses import fields, asdict, astuple, replace

for f in fields(InventoryItem):
    print(f.name, f.type)

d = asdict(item)          # Convert to dict
t = astuple(item)         # Convert to tuple
new = replace(item, x=5)  # Create copy with changes
```
