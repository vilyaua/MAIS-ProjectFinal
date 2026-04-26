# Common Design Patterns in Python

## Creational Patterns

### Singleton
```python
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### Factory Method
```python
from abc import ABC, abstractmethod

class Creator(ABC):
    @abstractmethod
    def factory_method(self) -> "Product": ...

    def some_operation(self) -> str:
        product = self.factory_method()
        return product.operation()

class ConcreteCreator(Creator):
    def factory_method(self) -> "Product":
        return ConcreteProduct()
```

### Builder
```python
class QueryBuilder:
    def __init__(self):
        self._table = ""
        self._conditions = []
        self._limit = None

    def from_table(self, table: str) -> "QueryBuilder":
        self._table = table
        return self

    def where(self, condition: str) -> "QueryBuilder":
        self._conditions.append(condition)
        return self

    def limit(self, n: int) -> "QueryBuilder":
        self._limit = n
        return self

    def build(self) -> str:
        query = f"SELECT * FROM {self._table}"
        if self._conditions:
            query += " WHERE " + " AND ".join(self._conditions)
        if self._limit:
            query += f" LIMIT {self._limit}"
        return query
```

## Structural Patterns

### Decorator (Function-based)
```python
import functools
import time

def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
```

### Adapter
```python
class OldSystem:
    def specific_request(self) -> str:
        return "old data format"

class Adapter:
    def __init__(self, old: OldSystem):
        self._old = old

    def request(self) -> dict:
        data = self._old.specific_request()
        return {"data": data, "format": "new"}
```

### Facade
```python
class Facade:
    def __init__(self):
        self._subsystem1 = Subsystem1()
        self._subsystem2 = Subsystem2()

    def operation(self) -> str:
        results = []
        results.append(self._subsystem1.operation1())
        results.append(self._subsystem2.operation1())
        return "\n".join(results)
```

## Behavioral Patterns

### Strategy
```python
from typing import Protocol

class SortStrategy(Protocol):
    def sort(self, data: list) -> list: ...

class QuickSort:
    def sort(self, data: list) -> list:
        return sorted(data)  # simplified

class BubbleSort:
    def sort(self, data: list) -> list:
        result = data[:]
        for i in range(len(result)):
            for j in range(len(result) - 1):
                if result[j] > result[j + 1]:
                    result[j], result[j + 1] = result[j + 1], result[j]
        return result

class Sorter:
    def __init__(self, strategy: SortStrategy):
        self._strategy = strategy

    def sort(self, data: list) -> list:
        return self._strategy.sort(data)
```

### Observer
```python
class EventSystem:
    def __init__(self):
        self._listeners: dict[str, list] = {}

    def subscribe(self, event: str, callback):
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event: str, data=None):
        for callback in self._listeners.get(event, []):
            callback(data)

events = EventSystem()
events.subscribe("user_created", lambda user: print(f"Welcome {user}!"))
events.emit("user_created", "Alice")
```

### Iterator
```python
class Range:
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

    def __iter__(self):
        current = self.start
        while current < self.end:
            yield current
            current += 1

for i in Range(1, 5):
    print(i)  # 1, 2, 3, 4
```

### Context Manager (Resource Management)
```python
class DatabaseConnection:
    def __enter__(self):
        self.conn = create_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        return False  # Don't suppress exceptions

with DatabaseConnection() as conn:
    conn.execute("SELECT 1")
```

### Template Method
```python
from abc import ABC, abstractmethod

class DataMiner(ABC):
    def mine(self, path: str):
        file = self.open_file(path)
        data = self.extract_data(file)
        analysis = self.analyze(data)
        self.send_report(analysis)

    @abstractmethod
    def open_file(self, path: str): ...

    @abstractmethod
    def extract_data(self, file): ...

    def analyze(self, data):
        return {"count": len(data)}

    def send_report(self, analysis):
        print(analysis)
```

## Python-Specific Patterns

### Mixin Classes
```python
class JsonMixin:
    def to_json(self) -> str:
        import json
        return json.dumps(self.__dict__)

class LogMixin:
    def log(self, message: str):
        print(f"[{self.__class__.__name__}] {message}")

class User(JsonMixin, LogMixin):
    def __init__(self, name: str):
        self.name = name

user = User("Alice")
user.log("created")      # [User] created
user.to_json()           # {"name": "Alice"}
```

### Registry Pattern
```python
_registry: dict[str, type] = {}

def register(cls):
    _registry[cls.__name__] = cls
    return cls

@register
class Handler:
    pass

def get_handler(name: str) -> type:
    return _registry[name]
```
