"""Tests for the JSON-backed todo CLI application."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from src.todo_app import TodoStore, run_cli


def run_command(args: list[str]) -> tuple[int, str]:
    """Run the CLI with captured stdout."""
    stdout = StringIO()
    status = run_cli(args, stdout=stdout)
    return status, stdout.getvalue()


def test_missing_storage_file_initializes_empty_list(tmp_path: Path) -> None:
    storage_file = tmp_path / "missing.json"

    store = TodoStore(storage_file)

    assert store.items == []
    assert not storage_file.exists()


def test_add_creates_incomplete_item_with_unique_id(tmp_path: Path) -> None:
    storage_file = tmp_path / "todos.json"

    status, output = run_command(["--file", str(storage_file), "add", "Buy milk"])
    store = TodoStore(storage_file)

    assert status == 0
    assert "Added todo 1: Buy milk" in output
    assert len(store.items) == 1
    assert store.items[0].id == 1
    assert store.items[0].description == "Buy milk"
    assert store.items[0].completed is False


def test_list_displays_all_items_with_status(tmp_path: Path) -> None:
    storage_file = tmp_path / "todos.json"
    run_command(["--file", str(storage_file), "add", "Buy milk"])
    run_command(["--file", str(storage_file), "add", "Read book"])
    run_command(["--file", str(storage_file), "complete", "2"])

    status, output = run_command(["--file", str(storage_file), "list"])

    assert status == 0
    assert "1. [incomplete] Buy milk" in output
    assert "2. [completed] Read book" in output


def test_complete_marks_item_completed(tmp_path: Path) -> None:
    storage_file = tmp_path / "todos.json"
    run_command(["--file", str(storage_file), "add", "Buy milk"])

    status, output = run_command(["--file", str(storage_file), "complete", "1"])
    store = TodoStore(storage_file)

    assert status == 0
    assert "Completed todo 1: Buy milk" in output
    assert store.items[0].completed is True


def test_delete_removes_item(tmp_path: Path) -> None:
    storage_file = tmp_path / "todos.json"
    run_command(["--file", str(storage_file), "add", "Buy milk"])
    run_command(["--file", str(storage_file), "add", "Read book"])

    status, output = run_command(["--file", str(storage_file), "delete", "2"])
    store = TodoStore(storage_file)

    assert status == 0
    assert "Deleted todo 2: Read book" in output
    assert [item.id for item in store.items] == [1]


def test_invalid_command_returns_error_without_crashing(tmp_path: Path) -> None:
    storage_file = tmp_path / "todos.json"

    status, _ = run_command(["--file", str(storage_file), "unknown"])

    assert status == 2


def test_missing_parameter_returns_error_without_crashing(tmp_path: Path) -> None:
    storage_file = tmp_path / "todos.json"

    status, _ = run_command(["--file", str(storage_file), "add"])

    assert status == 2


def test_unknown_item_error_message(tmp_path: Path) -> None:
    storage_file = tmp_path / "todos.json"

    status, output = run_command(["--file", str(storage_file), "complete", "99"])

    assert status == 1
    assert "Error: Todo item with ID 99 was not found." in output


def test_changes_persist_after_restart(tmp_path: Path) -> None:
    storage_file = tmp_path / "todos.json"
    run_command(["--file", str(storage_file), "add", "Buy milk"])
    run_command(["--file", str(storage_file), "add", "Read book"])
    run_command(["--file", str(storage_file), "complete", "1"])
    run_command(["--file", str(storage_file), "delete", "2"])

    reloaded_store = TodoStore(storage_file)
    raw_data = json.loads(storage_file.read_text(encoding="utf-8"))

    assert len(reloaded_store.items) == 1
    assert reloaded_store.items[0].id == 1
    assert reloaded_store.items[0].description == "Buy milk"
    assert reloaded_store.items[0].completed is True
    assert raw_data == [
        {"id": 1, "description": "Buy milk", "completed": True},
    ]


def test_empty_description_is_rejected(tmp_path: Path) -> None:
    storage_file = tmp_path / "todos.json"

    status, output = run_command(["--file", str(storage_file), "add", "   "])

    assert status == 1
    assert "Error: Task description cannot be empty." in output


def test_invalid_json_storage_reports_clear_error(tmp_path: Path) -> None:
    storage_file = tmp_path / "todos.json"
    storage_file.write_text("not-json", encoding="utf-8")

    status, output = run_command(["--file", str(storage_file), "list"])

    assert status == 1
    assert "contains invalid JSON" in output
