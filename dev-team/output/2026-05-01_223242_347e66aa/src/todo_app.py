"""Core todo application logic and CLI helpers."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence, TextIO


class TodoError(Exception):
    """Base exception for todo application errors."""


class TodoNotFoundError(TodoError):
    """Raised when a todo item cannot be found."""


class StorageError(TodoError):
    """Raised when todo storage cannot be read or written safely."""


@dataclass(slots=True)
class TodoItem:
    """A single todo item."""

    id: int
    description: str
    completed: bool = False


class TodoStore:
    """JSON-backed storage for todo items."""

    def __init__(self, storage_path: str | Path = "todos.json") -> None:
        self.storage_path = Path(storage_path)
        self._items: list[TodoItem] = []
        self.load()

    @property
    def items(self) -> list[TodoItem]:
        """Return a copy of stored todo items."""
        return list(self._items)

    def load(self) -> None:
        """Load todo items from JSON storage, or initialize empty storage."""
        if not self.storage_path.exists():
            self._items = []
            return

        try:
            with self.storage_path.open("r", encoding="utf-8") as file_handle:
                raw_data = json.load(file_handle)
        except json.JSONDecodeError as exc:
            raise StorageError(
                f"Storage file '{self.storage_path}' contains invalid JSON."
            ) from exc
        except OSError as exc:
            raise StorageError(f"Could not read storage file '{self.storage_path}': {exc}") from exc

        if not isinstance(raw_data, list):
            raise StorageError(f"Storage file '{self.storage_path}' must contain a JSON list.")

        loaded_items: list[TodoItem] = []
        try:
            for item in raw_data:
                if not isinstance(item, dict):
                    raise ValueError("Each todo item must be a JSON object.")
                todo_id = item["id"]
                description = item["description"]
                completed = item.get("completed", False)
                if not isinstance(todo_id, int) or todo_id <= 0:
                    raise ValueError("Todo item IDs must be positive integers.")
                if not isinstance(description, str) or not description.strip():
                    raise ValueError("Todo descriptions must be non-empty strings.")
                if not isinstance(completed, bool):
                    raise ValueError("Todo completion status must be boolean.")
                loaded_items.append(
                    TodoItem(
                        id=todo_id,
                        description=description,
                        completed=completed,
                    )
                )
        except (KeyError, ValueError) as exc:
            raise StorageError(
                f"Storage file '{self.storage_path}' has invalid todo data: {exc}"
            ) from exc

        ids = [item.id for item in loaded_items]
        if len(ids) != len(set(ids)):
            raise StorageError(f"Storage file '{self.storage_path}' contains duplicate todo IDs.")

        self._items = loaded_items

    def save(self) -> None:
        """Persist todo items to JSON storage."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with self.storage_path.open("w", encoding="utf-8") as file_handle:
                json.dump(
                    [asdict(item) for item in self._items],
                    file_handle,
                    indent=2,
                )
                file_handle.write("\n")
        except OSError as exc:
            raise StorageError(
                f"Could not write storage file '{self.storage_path}': {exc}"
            ) from exc

    def add(self, description: str) -> TodoItem:
        """Add a new incomplete todo item."""
        normalized_description = description.strip()
        if not normalized_description:
            raise ValueError("Task description cannot be empty.")

        next_id = max((item.id for item in self._items), default=0) + 1
        item = TodoItem(
            id=next_id,
            description=normalized_description,
            completed=False,
        )
        self._items.append(item)
        self.save()
        return item

    def complete(self, todo_id: int) -> TodoItem:
        """Mark a todo item as completed by ID."""
        item = self._find(todo_id)
        item.completed = True
        self.save()
        return item

    def delete(self, todo_id: int) -> TodoItem:
        """Delete a todo item by ID."""
        item = self._find(todo_id)
        self._items = [existing for existing in self._items if existing.id != todo_id]
        self.save()
        return item

    def _find(self, todo_id: int) -> TodoItem:
        if todo_id <= 0:
            raise TodoNotFoundError(f"Todo ID must be a positive integer: {todo_id}")
        for item in self._items:
            if item.id == todo_id:
                return item
        raise TodoNotFoundError(f"Todo item with ID {todo_id} was not found.")


def format_item(item: TodoItem) -> str:
    """Format one todo item for list output."""
    status = "completed" if item.completed else "incomplete"
    return f"{item.id}. [{status}] {item.description}"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="todo",
        description="Manage todo items stored in a JSON file.",
    )
    parser.add_argument(
        "--file",
        default=os.environ.get("TODO_FILE", "todos.json"),
        help="Path to JSON storage file (default: todos.json or TODO_FILE).",
    )

    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Add a new todo item.")
    add_parser.add_argument(
        "description",
        nargs="+",
        help="Task description. Quote it when it contains spaces.",
    )

    subparsers.add_parser("list", help="List all todo items.")

    complete_parser = subparsers.add_parser(
        "complete",
        help="Mark a todo item as completed.",
    )
    complete_parser.add_argument("id", type=int, help="ID of todo item to complete.")

    delete_parser = subparsers.add_parser("delete", help="Delete a todo item.")
    delete_parser.add_argument("id", type=int, help="ID of todo item to delete.")

    return parser


def execute_command(args: argparse.Namespace, stdout: TextIO) -> int:
    """Execute a parsed CLI command and write user-facing output."""
    try:
        store = TodoStore(args.file)

        if args.command == "add":
            description = " ".join(args.description)
            item = store.add(description)
            print(f"Added todo {item.id}: {item.description}", file=stdout)
        elif args.command == "list":
            items = store.items
            if not items:
                print("No todo items found.", file=stdout)
            else:
                for item in items:
                    print(format_item(item), file=stdout)
        elif args.command == "complete":
            item = store.complete(args.id)
            print(f"Completed todo {item.id}: {item.description}", file=stdout)
        elif args.command == "delete":
            item = store.delete(args.id)
            print(f"Deleted todo {item.id}: {item.description}", file=stdout)
        else:
            print("Error: missing command. Use add, list, complete, or delete.", file=stdout)
            return 2
    except (TodoError, ValueError) as exc:
        print(f"Error: {exc}", file=stdout)
        return 1

    return 0


def run_cli(
    argv: Sequence[str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the todo CLI once, or start an interactive shell when no command is given."""
    if argv is None:
        argv = sys.argv[1:]
    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr

    if len(argv) == 0:
        return run_interactive(stdout=stdout, stderr=stderr)

    parser = build_parser()
    try:
        args = parser.parse_args(list(argv))
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2

    return execute_command(args, stdout)


def run_interactive(stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    """Run an interactive todo prompt until the user exits."""
    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr

    print("Todo CLI. Enter commands: add, list, complete, delete, or exit.", file=stdout)
    storage_file = os.environ.get("TODO_FILE", "todos.json")

    while True:
        try:
            line = input("todo> ").strip()
        except EOFError:
            print(file=stdout)
            return 0
        except KeyboardInterrupt:
            print("\nExiting.", file=stdout)
            return 130

        if not line:
            continue
        if line.lower() in {"exit", "quit"}:
            return 0

        try:
            command_args = shlex.split(line)
        except ValueError as exc:
            print(f"Error: could not parse command: {exc}", file=stdout)
            continue

        status = run_cli(["--file", storage_file, *command_args], stdout, stderr)
        if status not in (0, 1, 2):
            return status


def main() -> int:
    """Application entry point."""
    return run_cli()


if __name__ == "__main__":
    raise SystemExit(main())
