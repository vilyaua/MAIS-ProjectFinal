# Python Async/Await

## Basics
```python
import asyncio

async def main():
    print('hello')
    await asyncio.sleep(1)
    print('world')

asyncio.run(main())
```

## Coroutines
```python
async def fetch_data(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

## Concurrent Execution
```python
async def main():
    # Run concurrently
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3"),
    )

    # With TaskGroup (Python 3.11+)
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_data("url1"))
        task2 = tg.create_task(fetch_data("url2"))
    # All tasks completed here
    result1 = task1.result()
    result2 = task2.result()
```

## Tasks
```python
async def main():
    task = asyncio.create_task(long_operation())
    # Do other work while task runs...
    result = await task
```

## Timeouts
```python
async def main():
    try:
        async with asyncio.timeout(5.0):
            result = await long_operation()
    except TimeoutError:
        print("Operation timed out")

    # Or with wait_for
    try:
        result = await asyncio.wait_for(long_operation(), timeout=5.0)
    except asyncio.TimeoutError:
        print("Timed out")
```

## Async Iterators
```python
class AsyncRange:
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop

    def __aiter__(self):
        self.current = self.start
        return self

    async def __anext__(self):
        if self.current >= self.stop:
            raise StopAsyncIteration
        value = self.current
        self.current += 1
        await asyncio.sleep(0.1)
        return value

async def main():
    async for i in AsyncRange(0, 5):
        print(i)
```

## Async Generators
```python
async def async_range(start, stop):
    for i in range(start, stop):
        await asyncio.sleep(0.1)
        yield i

async def main():
    async for i in async_range(0, 5):
        print(i)
```

## Async Context Managers
```python
class AsyncDatabase:
    async def __aenter__(self):
        self.conn = await create_connection()
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.conn.close()
        return False

async def main():
    async with AsyncDatabase() as conn:
        await conn.execute("SELECT 1")
```

## Synchronization
```python
# Lock
lock = asyncio.Lock()
async with lock:
    # exclusive access

# Semaphore
sem = asyncio.Semaphore(10)
async with sem:
    # max 10 concurrent

# Event
event = asyncio.Event()
await event.wait()    # Block until set
event.set()           # Signal
event.clear()         # Reset

# Queue
queue = asyncio.Queue(maxsize=100)
await queue.put(item)
item = await queue.get()
```

## Best Practices

1. Use `asyncio.run()` as the single entry point
2. Never mix `asyncio.run()` with manual loop management
3. Use `asyncio.gather()` or `TaskGroup` for concurrent tasks
4. Always set timeouts on I/O operations
5. Use `async with` for resource management
6. Don't call blocking functions in async code — use `asyncio.to_thread()`

```python
# Run blocking code in a thread
result = await asyncio.to_thread(blocking_io_function, arg1, arg2)
```
