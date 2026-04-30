import os
import json
import pytest
from src import todo_cli

JSON_FILE = 'test_todos.json'


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: remove test JSON file if exists
    if os.path.exists(JSON_FILE):
        os.remove(JSON_FILE)
    yield
    # Teardown: remove test JSON file if exists
    if os.path.exists(JSON_FILE):
        os.remove(JSON_FILE)


def test_add_and_list(capsys):
    manager = todo_cli.TodoManager(JSON_FILE)
    manager.add("Test task 1")
    manager.add("Test task 2")

    captured = capsys.readouterr()
    assert "Added task 1: Test task 1" in captured.out
    assert "Added task 2: Test task 2" in captured.out

    # List and capture output
    manager.list()
    captured_list = capsys.readouterr()
    assert "[1] Test task 1 - Pending" in captured_list.out
    assert "[2] Test task 2 - Pending" in captured_list.out


def test_complete_and_delete(capsys):
    manager = todo_cli.TodoManager(JSON_FILE)
    manager.add("Another task")

    # Complete task
    manager.complete(1)
    captured_complete = capsys.readouterr()
    assert "Task 1 marked as completed." in captured_complete.out

    # Complete non-existent
    manager.complete(99)
    captured_err = capsys.readouterr()
    assert "Error: No task found with ID 99." in captured_err.out

    # Delete task
    manager.delete(1)
    captured_delete = capsys.readouterr()
    assert "Task 1 deleted." in captured_delete.out

    # Delete non-existent
    manager.delete(99)
    captured_err_del = capsys.readouterr()
    assert "Error: No task found with ID 99." in captured_err_del.out


def test_add_empty_description(capsys):
    manager = todo_cli.TodoManager(JSON_FILE)
    manager.add("")
    captured = capsys.readouterr()
    assert "Error: Task description cannot be empty." in captured.out


def test_corrupted_file(monkeypatch, capsys):
    # Write corrupted JSON
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        f.write('not a json')

    # Simulate user input 'y' for reinitialize
    def fake_input(prompt):
        return 'y'

    monkeypatch.setattr('builtins.input', fake_input)

    manager = todo_cli.TodoManager(JSON_FILE)
    captured = capsys.readouterr()
    assert "Storage file is corrupted or invalid." in captured.out
    # Should create an empty todos list after reinit
    assert manager.todos == []


def test_file_not_found_creates_file():
    if os.path.exists(JSON_FILE):
        os.remove(JSON_FILE)

    manager = todo_cli.TodoManager(JSON_FILE)
    # Initially no file
    assert not os.path.exists(JSON_FILE)

    # Add triggers file creation
    manager.add("New task")
    assert os.path.exists(JSON_FILE)


def test_invalid_task_id(capsys):
    manager = todo_cli.TodoManager(JSON_FILE)
    manager.add("Task for testing id")

    # Complete with invalid ID
    manager.complete(999)
    captured = capsys.readouterr()
    assert "Error: No task found with ID 999." in captured.out

    # Delete with invalid ID
    manager.delete(999)
    captured_del = capsys.readouterr()
    assert "Error: No task found with ID 999." in captured_del.out


if __name__ == '__main__':
    pytest.main()  
