# Python argparse Module

## Overview

`argparse` is the standard library module for parsing command-line arguments. It generates help messages, handles type conversion, and supports subcommands.

## Basic Usage

```python
import argparse

parser = argparse.ArgumentParser(description="My CLI tool")
parser.add_argument("input", help="Input file path")
parser.add_argument("-o", "--output", default="out.txt", help="Output file")
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
parser.add_argument("-n", "--count", type=int, default=10, help="Number of items")
args = parser.parse_args()
```

## Argument Types

- **Positional**: `parser.add_argument("filename")` — required
- **Optional**: `parser.add_argument("-f", "--file")` — optional flag
- **Boolean**: `parser.add_argument("--debug", action="store_true")`
- **Choices**: `parser.add_argument("--mode", choices=["fast", "slow"])`
- **Multiple values**: `parser.add_argument("--items", nargs="+", type=int)`

## Subcommands

```python
subparsers = parser.add_subparsers(dest="command")
add_parser = subparsers.add_parser("add", help="Add item")
add_parser.add_argument("name")
list_parser = subparsers.add_parser("list", help="List items")
```

## Best Practices

- Always include `description` in `ArgumentParser`
- Use `type=` for automatic validation
- Provide sensible `default=` values
- Add `help=` to every argument
- Use `metavar=` for cleaner help output
