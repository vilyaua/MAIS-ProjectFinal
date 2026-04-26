# Python re Module — Regular Expressions

## Core Functions

```python
import re

re.match(r"c", "abcdef")       # None — matches START only
re.search(r"c", "abcdef")      # Match at index 2
re.fullmatch(r"p.*n", "python") # Entire string must match

re.findall(r'\bf[a-z]*', 'which foot fell fastest')
# ['foot', 'fell', 'fastest']

re.sub(r'\d+', 'X', 'abc123def456')  # 'abcXdefX'

re.split(r'\W+', 'Words, words, words.')
# ['Words', 'words', 'words', '']
```

## Compile for Reuse
```python
pattern = re.compile(r'\d+')
pattern.findall('abc123def456')  # ['123', '456']
```

## Match Object
```python
m = re.search(r'(\w+) (\w+)', 'Isaac Newton')
m.group(0)    # 'Isaac Newton' (entire match)
m.group(1)    # 'Isaac'
m.group(2)    # 'Newton'
m.groups()    # ('Isaac', 'Newton')
m.start()     # Start index
m.end()       # End index
m.span()      # (start, end) tuple
```

## Common Patterns

| Pattern | Matches |
|---------|---------|
| `.` | Any character (except newline) |
| `^` | Start of string |
| `$` | End of string |
| `*` | 0 or more |
| `+` | 1 or more |
| `?` | 0 or 1 |
| `{m,n}` | m to n repetitions |
| `\d` | Digit [0-9] |
| `\w` | Word character [a-zA-Z0-9_] |
| `\s` | Whitespace |
| `\b` | Word boundary |
| `[abc]` | Character set |
| `(...)` | Capturing group |
| `(?:...)` | Non-capturing group |
| `A\|B` | Alternation |

## Named Groups
```python
m = re.search(r'(?P<first>\w+) (?P<last>\w+)', 'Isaac Newton')
m.group('first')   # 'Isaac'
m.groupdict()      # {'first': 'Isaac', 'last': 'Newton'}
```

## Flags
```python
re.IGNORECASE  # Case-insensitive
re.MULTILINE   # ^ and $ match line boundaries
re.DOTALL      # . matches newlines
re.VERBOSE     # Allow whitespace and comments
```

## Sub with Function
```python
def dashrepl(m):
    return ' ' if m.group(0) == '-' else '-'
re.sub('-{1,2}', dashrepl, 'pro----gram-files')
```

Always use raw strings (`r"..."`) for regex patterns.
