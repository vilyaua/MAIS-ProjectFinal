# Python collections Module

## Counter
```python
from collections import Counter

cnt = Counter(['red', 'blue', 'red', 'green', 'blue', 'blue'])
# Counter({'blue': 3, 'red': 2, 'green': 1})

cnt.most_common(2)   # [('blue', 3), ('red', 2)]
cnt.elements()       # Iterator repeating each by count
cnt.total()          # Sum of all counts
# Supports +, -, &, | operations
```

## defaultdict
```python
from collections import defaultdict

d = defaultdict(list)
for k, v in [('a', 1), ('b', 2), ('a', 3)]:
    d[k].append(v)
# {'a': [1, 3], 'b': [2]}

d = defaultdict(int)
for word in 'mississippi':
    d[word] += 1
```

## deque
Double-ended queue with O(1) appends and pops from either end.
```python
from collections import deque

d = deque('ghi')
d.append('j')        # Add right
d.appendleft('f')    # Add left
d.pop()              # Remove right
d.popleft()          # Remove left
d.rotate(1)          # Rotate right

bounded = deque(maxlen=3)
bounded.extend([1, 2, 3, 4])  # deque([2, 3, 4])
```

## namedtuple
```python
from collections import namedtuple

Point = namedtuple('Point', ['x', 'y'])
p = Point(11, y=22)
p.x + p.y    # 33
p[0] + p[1]  # 33

p._asdict()           # {'x': 11, 'y': 22}
p._replace(x=100)     # Point(x=100, y=22)
Point._make([1, 2])   # Point(x=1, y=2)

Account = namedtuple('Account', ['type', 'balance'], defaults=[0])
```

## OrderedDict
```python
from collections import OrderedDict

d = OrderedDict.fromkeys('abcde')
d.move_to_end('b')          # Move to end
d.move_to_end('b', last=False)  # Move to beginning
d.popitem(last=True)        # LIFO or FIFO
```

## ChainMap
```python
from collections import ChainMap

baseline = {'music': 'bach', 'art': 'rembrandt'}
adjustments = {'art': 'van gogh', 'opera': 'carmen'}
combined = ChainMap(adjustments, baseline)
# Lookups search mappings successively; writes go to first
```
