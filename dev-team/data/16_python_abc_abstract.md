# Python abc Module — Abstract Base Classes

## Basic Usage
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        """Calculate the area of the shape."""
        ...

    @abstractmethod
    def perimeter(self) -> float:
        """Calculate the perimeter of the shape."""
        ...

    def description(self) -> str:
        """Non-abstract method with default implementation."""
        return f"{self.__class__.__name__}: area={self.area():.2f}"

class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius

    def area(self) -> float:
        return 3.14159 * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * 3.14159 * self.radius

# Shape()  # TypeError: Can't instantiate abstract class
c = Circle(5)
c.area()       # 78.54
c.description()  # "Circle: area=78.54"
```

## Abstract Properties
```python
class Animal(ABC):
    @property
    @abstractmethod
    def sound(self) -> str: ...

class Dog(Animal):
    @property
    def sound(self) -> str:
        return "Woof"
```

## ABCMeta (Alternative)
```python
from abc import ABCMeta, abstractmethod

class MyABC(metaclass=ABCMeta):
    @abstractmethod
    def method(self): ...
```

## Register Virtual Subclasses
```python
class MyABC(ABC):
    @abstractmethod
    def method(self): ...

class ThirdPartyClass:
    def method(self):
        return "implemented"

MyABC.register(ThirdPartyClass)
isinstance(ThirdPartyClass(), MyABC)  # True
```

## __subclasshook__
```python
class Closable(ABC):
    @abstractmethod
    def close(self): ...

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Closable:
            if hasattr(C, 'close'):
                return True
        return NotImplemented
```
