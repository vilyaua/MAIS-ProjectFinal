# Python contextlib Module

## @contextmanager
```python
from contextlib import contextmanager

@contextmanager
def managed_resource(*args, **kwds):
    resource = acquire_resource(*args, **kwds)
    try:
        yield resource
    finally:
        release_resource(resource)

with managed_resource(timeout=3600) as resource:
    pass  # resource released at end
```

## @asynccontextmanager
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_connection():
    conn = await acquire_db_connection()
    try:
        yield conn
    finally:
        await release_db_connection(conn)
```

## closing
```python
from contextlib import closing
from urllib.request import urlopen

with closing(urlopen('https://www.python.org')) as page:
    for line in page:
        print(line)
```

## suppress
```python
from contextlib import suppress

with suppress(FileNotFoundError):
    os.remove('somefile.tmp')
```

## redirect_stdout / redirect_stderr
```python
import io
from contextlib import redirect_stdout

with redirect_stdout(io.StringIO()) as f:
    help(pow)
s = f.getvalue()
```

## ExitStack
```python
from contextlib import ExitStack

with ExitStack() as stack:
    files = [stack.enter_context(open(fname)) for fname in filenames]
    # All files closed at end

# Methods: enter_context(), push(), callback(), pop_all(), close()
```

## nullcontext
```python
from contextlib import nullcontext

# No-op context manager for optional use
cm = nullcontext(default_value)
with cm as value:
    pass  # value == default_value
```

## chdir
```python
from contextlib import chdir

with chdir('/tmp'):
    pass  # Working dir changed temporarily
```
