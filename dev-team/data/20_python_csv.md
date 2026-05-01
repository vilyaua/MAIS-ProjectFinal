# Python csv Module

## Overview

The `csv` module provides classes for reading and writing CSV (Comma Separated Values) files.

## Reading CSV

```python
import csv

with open("data.csv", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        print(row)  # list of strings

# DictReader — rows as dictionaries
with open("data.csv", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row["name"], row["age"])
```

## Writing CSV

```python
with open("output.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "age", "city"])
    writer.writerows([["Alice", 30, "NYC"], ["Bob", 25, "LA"]])

# DictWriter
with open("output.csv", "w", newline="") as f:
    fields = ["name", "age"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerow({"name": "Alice", "age": 30})
```

## Dialects and Formatting

- `delimiter=","` — field separator
- `quotechar='"'` — quoting character
- `quoting=csv.QUOTE_MINIMAL` — when to quote
- `csv.Sniffer().sniff(sample)` — auto-detect format

## Best Practices

- Always use `newline=""` when opening CSV files
- Use `DictReader`/`DictWriter` for readability
- Handle encoding: `open(f, encoding="utf-8")`
- Validate data types after reading (all values are strings)
