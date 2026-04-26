# Python unittest Module

## Basic Example
```python
import unittest

class TestStringMethods(unittest.TestCase):
    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()
```

## Setup and Teardown
```python
class WidgetTestCase(unittest.TestCase):
    def setUp(self):
        self.widget = Widget('The widget')

    def tearDown(self):
        self.widget.dispose()

    @classmethod
    def setUpClass(cls):
        pass  # Called once before all tests

    @classmethod
    def tearDownClass(cls):
        pass  # Called once after all tests
```

## Common Assert Methods

| Method | Checks |
|--------|--------|
| `assertEqual(a, b)` | `a == b` |
| `assertNotEqual(a, b)` | `a != b` |
| `assertTrue(x)` | `bool(x) is True` |
| `assertFalse(x)` | `bool(x) is False` |
| `assertIs(a, b)` | `a is b` |
| `assertIsNone(x)` | `x is None` |
| `assertIn(a, b)` | `a in b` |
| `assertIsInstance(a, b)` | `isinstance(a, b)` |
| `assertRaises(exc)` | Exception raised |
| `assertAlmostEqual(a, b)` | `round(a-b, 7) == 0` |
| `assertGreater(a, b)` | `a > b` |
| `assertRegex(s, r)` | Regex matches |

## Exception Testing
```python
with self.assertRaises(ValueError) as cm:
    int('not a number')
self.assertEqual(cm.exception.args[0], "invalid literal...")
```

## Skipping Tests
```python
@unittest.skip("reason")
def test_nothing(self): ...

@unittest.skipIf(condition, "reason")
def test_feature(self): ...

@unittest.expectedFailure
def test_broken(self): ...
```

## Subtests
```python
def test_even(self):
    for i in range(0, 6):
        with self.subTest(i=i):
            self.assertEqual(i % 2, 0)
```

## Test Discovery
```bash
python -m unittest discover -s project_directory -p "*_test.py"
python -m unittest -v test_module
python -m unittest -k pattern
```

## Async Testing
```python
from unittest import IsolatedAsyncioTestCase

class AsyncTest(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.connection = await create_connection()

    async def test_fetch(self):
        result = await self.connection.fetch('SELECT 1')
        self.assertEqual(result, 1)
```
