# Python sqlite3 Module

## Overview

`sqlite3` provides a DB-API 2.0 interface to SQLite databases. No external server needed — the database is a single file.

## Basic Usage

```python
import sqlite3

conn = sqlite3.connect("mydb.sqlite")
conn.row_factory = sqlite3.Row  # access columns by name
cursor = conn.cursor()

# Create table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Insert
cursor.execute("INSERT INTO tasks (title) VALUES (?)", ("Buy groceries",))
conn.commit()

# Query
cursor.execute("SELECT * FROM tasks WHERE done = ?", (False,))
rows = cursor.fetchall()
for row in rows:
    print(row["id"], row["title"])

# Update
cursor.execute("UPDATE tasks SET done = ? WHERE id = ?", (True, 1))
conn.commit()

# Delete
cursor.execute("DELETE FROM tasks WHERE id = ?", (1,))
conn.commit()

conn.close()
```

## Context Manager

```python
with sqlite3.connect("mydb.sqlite") as conn:
    conn.execute("INSERT INTO tasks (title) VALUES (?)", ("Task",))
    # auto-commits on success, rolls back on exception
```

## Best Practices

- Always use parameterized queries (`?`) — never string formatting (SQL injection)
- Use `conn.row_factory = sqlite3.Row` for named column access
- Use context managers for automatic commit/rollback
- Use `AUTOINCREMENT` for primary keys
- Close connections when done
- Use `IF NOT EXISTS` in CREATE TABLE for idempotency
