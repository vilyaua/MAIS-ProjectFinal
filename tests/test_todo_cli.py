import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import stat

# We will run subprocess commands to simulate CLI usage.
# To isolate tests, we will temporarily override the STORAGE_FILE to a temp file.

# Path to the CLI script
SCRIPT_PATH = Path(__file__).parent.parent / "src" / "todo_cli.py"


def run_cli(args):
    """Run the CLI with args list and capture output."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)] + args,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def subprocess_run(cmd):
    # Run the script using python interpreter to avoid exec format error
    full_cmd = [sys.executable] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def test_add_list_delete_complete():
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_json = Path(tmpdir) / "todo_tasks.json"
        # Patch storage file path by copying script and changing STORAGE_FILE
        script_code = SCRIPT_PATH.read_text()
        # Replace STORAGE_FILE = Path(...) with the temp JSON path
        modified_code = script_code.replace(
            'STORAGE_FILE = Path("todo_tasks.json")',
            f'STORAGE_FILE = Path(r"{str(temp_json)}")'
        )

        temp_script = Path(tmpdir) / "todo_cli.py"
        temp_script.write_text(modified_code)

        # Add a task
        out, err, code = subprocess_run([str(temp_script), "add", "Test task 1"])
        assert code == 0
        assert "Added task 1: Test task 1" in out

        # Add another task
        out, err, code = subprocess_run([str(temp_script), "add", "Test task 2"])
        assert code == 0
        assert "Added task 2: Test task 2" in out

        # List all tasks
        out, err, code = subprocess_run([str(temp_script), "list"])
        assert code == 0
        assert "[ ] 1: Test task 1" in out
        assert "[ ] 2: Test task 2" in out

        # Complete task 1
        out, err, code = subprocess_run([str(temp_script), "complete", "1"])
        assert code == 0
        assert "Marked task 1 as completed." in out

        # List again
        out, err, code = subprocess_run([str(temp_script), "list"])
        assert code == 0
        assert "[x] 1: Test task 1" in out

        # Complete a non-existent task
        out, err, code = subprocess_run([str(temp_script), "complete", "999"])
        assert code != 0
        assert "No task with ID 999 found." in out

        # Delete task 2
        out, err, code = subprocess_run([str(temp_script), "delete", "2"])
        assert code == 0
        assert "Deleted task 2." in out

        # Delete a non-existent task
        out, err, code = subprocess_run([str(temp_script), "delete", "999"])
        assert code != 0
        assert "No task with ID 999 found." in out

        # List again
        out, err, code = subprocess_run([str(temp_script), "list"])
        assert code == 0
        assert "[x] 1: Test task 1" in out
        assert "2:" not in out


def test_invalid_arguments():
    # Missing required description for add command
    out, err, code = run_cli(["add"])
    assert code != 0
    assert "error" in err.lower() or "usage" in err.lower()

    # Missing ID for complete command
    out, err, code = run_cli(["complete"])
    assert code != 0
    assert "error" in err.lower() or "usage" in err.lower()

    # Missing ID for delete command
    out, err, code = run_cli(["delete"])
    assert code != 0
    assert "error" in err.lower() or "usage" in err.lower()


def test_corrupted_json_recovery():
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_json = Path(tmpdir) / "todo_tasks.json"
        temp_json.write_text("{ malformed json... }")

        # Patch storage file path
        script_code = SCRIPT_PATH.read_text()
        modified_code = script_code.replace(
            'STORAGE_FILE = Path("todo_tasks.json")',
            f'STORAGE_FILE = Path(r"{str(temp_json)}")'
        )

        temp_script = Path(tmpdir) / "todo_cli.py"
        temp_script.write_text(modified_code)

        # Trying to list should print error and exit
        proc = subprocess.run(
            [sys.executable, str(temp_script), "list"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0
        assert "malformed json" in proc.stdout.lower() or "malformed json" in proc.stderr.lower()
