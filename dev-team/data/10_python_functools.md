# Python functools Module

## cache / lru_cache
```python
from functools import cache, lru_cache

@cache
def factorial(n):
    return n * factorial(n-1) if n else 1

@lru_cache(maxsize=32)
def get_pep(num):
    resource = f'https://peps.python.org/pep-{num:04d}'
    with urllib.request.urlopen(resource) as s:
        return s.read()

get_pep.cache_info()   # CacheInfo(hits=3, misses=8, ...)
get_pep.cache_clear()  # Clear cache
```

## partial
```python
from functools import partial

basetwo = partial(int, base=2)
basetwo('10010')  # 18
```

## reduce
```python
from functools import reduce

reduce(lambda x, y: x + y, [1, 2, 3, 4, 5])  # 15
reduce(lambda x, y: x + y, [1, 2, 3], 10)     # 16
```

## wraps
```python
from functools import wraps

def my_decorator(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        print('Calling decorated function')
        return f(*args, **kwds)
    return wrapper

@my_decorator
def example():
    """Docstring"""
    print('Called example function')

example.__name__  # 'example' (preserved by @wraps)
```

## singledispatch
```python
from functools import singledispatch

@singledispatch
def fun(arg):
    print(arg)

@fun.register
def _(arg: int):
    print(f"Integer: {arg}")

@fun.register
def _(arg: list):
    for i, elem in enumerate(arg):
        print(i, elem)
```

## total_ordering
```python
from functools import total_ordering

@total_ordering
class Student:
    def __eq__(self, other):
        return self.lastname == other.lastname

    def __lt__(self, other):
        return self.lastname < other.lastname
# Automatically generates __le__, __gt__, __ge__
```
