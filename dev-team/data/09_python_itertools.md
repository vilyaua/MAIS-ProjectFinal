# Python itertools Module

Memory-efficient iterator building blocks.

## Infinite Iterators
```python
from itertools import count, repeat, cycle

count(10)         # 10, 11, 12, ...
count(2.5, 0.5)   # 2.5, 3.0, 3.5, ...
repeat(10, 3)      # 10, 10, 10
cycle('ABCD')      # A, B, C, D, A, B, C, D, ...
```

## Selection & Filtering
```python
from itertools import islice, takewhile, dropwhile, compress

islice('ABCDEFG', 2, 4)     # C, D
takewhile(lambda x: x<5, [1,4,6,3])  # 1, 4
dropwhile(lambda x: x<5, [1,4,6,3])  # 6, 3
compress('ABCDEF', [1,0,1,0,1,1])    # A, C, E, F
```

## Chaining & Grouping
```python
from itertools import chain, groupby

chain('ABC', 'DEF')   # A, B, C, D, E, F
chain.from_iterable(['ABC', 'DEF'])  # Same

# Group consecutive elements (data must be sorted by key)
[k for k, g in groupby('AAAABBBCCD')]  # A, B, C, D
```

## Combinatoric Iterators
```python
from itertools import product, permutations, combinations, combinations_with_replacement

product('AB', 'xy')         # Ax, Ay, Bx, By
product('AB', repeat=2)     # AA, AB, BA, BB
permutations('ABC', 2)      # AB, AC, BA, BC, CA, CB
combinations('ABCD', 2)     # AB, AC, AD, BC, BD, CD
combinations_with_replacement('AB', 2)  # AA, AB, BB
```

## Transforming Iterators
```python
from itertools import starmap, accumulate, pairwise, batched

starmap(pow, [(2,5), (3,2)])     # 32, 9
accumulate([1,2,3,4,5])         # 1, 3, 6, 10, 15
pairwise('ABCDEFG')             # AB, BC, CD, DE, EF, FG
batched('ABCDEFG', 3)           # ABC, DEF, G
```

## Utility
```python
from itertools import tee, zip_longest

a, b = tee('ABC', 2)    # Two independent iterators
zip_longest('ABCD', 'xy', fillvalue='-')  # Ax, By, C-, D-
```
