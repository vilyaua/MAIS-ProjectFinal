import os
import json
import subprocess
import sys
import tempfile
import pytest

TODO_FILE = 'todo_tasks.json'


@pytest.fixture(autouse=True)
def run_around_tests():
    # Backup any existing TODO_FILE
    backup_exists = False
    if os.path.exists(TODO_FILE):
        os.rename(TODO_FILE, TODO_FILE + '.bak')
        backup_exists = True
    yield
    # Remove TODO_FILE after test
    if os.path.exists(TODO_FILE):
        os.remove(TODO_FILE)
    # Restore backup
    if backup_exists:
        os.rename(TODO_FILE + '.bak', TODO_FILE)


def run_command(args):
    cmd = [sys.executable, 'src/todo_cli.py'] + args
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result


def test_add_and_list():
    result_add = run_command(['add', 'Test task'])
    assert 'Task added with ID' in result_add.stdout

    result_list = run_command(['list'])
    assert 'Test task' in result_list.stdout
    assert 'Pending' in result_list.stdout


def test_add_empty_description():
    result = run_command(['add', '   '])
    assert 'Error: Task description cannot be empty.' in result.stdout


def test_complete_and_list():
    run_command(['add', 'Task to complete'])
    # Get task ID
    with open(TODO_FILE, 'r') as f:
        tasks = json.load(f)
    task_id = str(tasks[0]['id'])

    result_complete = run_command(['complete', task_id])
    assert f'Task {task_id} marked as completed.' in result_complete.stdout

    result_list = run_command(['list'])
    assert 'Done' in result_list.stdout


def test_complete_invalid_id():
    result = run_command(['complete', 'abc'])
    assert 'Error: Task ID must be a valid integer.' in result.stdout

    result = run_command(['complete', '99999'])
    assert 'Error: Task with ID 99999 not found.' in result.stdout


def test_delete_task():
    run_command(['add', 'Task to delete'])
    with open(TODO_FILE, 'r') as f:
        tasks = json.load(f)
    task_id = str(tasks[0]['id'])

    result_delete = run_command(['delete', task_id])
    assert f'Task {task_id} deleted.' in result_delete.stdout

    # Check list
    result_list = run_command(['list'])
    assert 'No tasks found.' in result_list.stdout


def test_delete_invalid_id():
    result = run_command(['delete', 'xyz'])
    assert 'Error: Task ID must be a valid integer.' in result.stdout

    result = run_command(['delete', '99999'])
    assert 'Error: Task with ID 99999 not found.' in result.stdout


def test_unknown_command():
    result = run_command(['foobar'])
    assert 'Error: Unknown command' in result.stdout
    assert 'To-Do CLI usage' in result.stdout


def test_no_command():
    result = run_command([])
    assert 'Error: No command provided.' in result.stdout
    assert 'To-Do CLI usage' in result.stdout


def test_help():
    result = run_command(['help'])
    assert 'To-Do CLI usage' in result.stdout
