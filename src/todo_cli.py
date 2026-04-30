import argparse
import json
import sys
from typing import List, Dict, Any
from pathlib import Path

STORAGE_FILE = Path("todo_tasks.json")


def load_tasks() -> List[Dict[str, Any]]:
    """
    Load tasks from the JSON storage file.
    If file does not exist, create it with empty list.
    Handle malformed JSON gracefully.
    """
    if not STORAGE_FILE.exists():
        save_tasks([])
        return []
    try:
        with STORAGE_FILE.open("r", encoding="utf-8") as f:
            tasks = json.load(f)
            # Validate that tasks is a list
            if not isinstance(tasks, list):
                print(f"Error: Storage data corrupted: expected a list but got {type(tasks).__name__}.")
                sys.exit(1)
            return tasks
    except json.JSONDecodeError:
        print("Error: Storage file contains malformed JSON.")
        sys.exit(1)
    except IOError as e:
        print(f"Error: Unable to read storage file: {e}")
        sys.exit(1)


def save_tasks(tasks: List[Dict[str, Any]]) -> None:
    """
    Save tasks list to the JSON storage file safely.
    """
    try:
        with STORAGE_FILE.open("w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
    except IOError as e:
        print(f"Error: Unable to write to storage file: {e}")
        sys.exit(1)


def generate_next_id(tasks: List[Dict[str, Any]]) -> int:
    """Generate the next unique ID for a new task."""
    if not tasks:
        return 1
    # Tasks have integer IDs
    max_id = max(task.get("id", 0) for task in tasks)
    return max_id + 1


def add_task(description: str) -> None:
    description = description.strip()
    if not description:
        print("Error: Task description cannot be empty.")
        sys.exit(1)

    tasks = load_tasks()
    new_id = generate_next_id(tasks)
    new_task = {
        "id": new_id,
        "description": description,
        "completed": False,
    }
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"Added task {new_id}: {description}")


def list_tasks() -> None:
    tasks = load_tasks()
    if not tasks:
        print("No tasks found.")
        return

    print("Todo Tasks:")
    for task in tasks:
        status = "[x]" if task.get("completed") else "[ ]"
        print(f"{status} {task['id']}: {task['description']}")


def find_task(tasks: List[Dict[str, Any]], task_id: int) -> Dict[str, Any]:
    for task in tasks:
        if task.get("id") == task_id:
            return task
    return {}


def complete_task(task_id: int) -> None:
    tasks = load_tasks()
    task = find_task(tasks, task_id)
    if not task:
        print(f"Error: No task with ID {task_id} found.")
        sys.exit(1)
    if task["completed"]:
        print(f"Task {task_id} is already completed.")
        return
    task["completed"] = True
    save_tasks(tasks)
    print(f"Marked task {task_id} as completed.")


def delete_task(task_id: int) -> None:
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t.get("id") != task_id]
    if len(tasks) == len(new_tasks):
        print(f"Error: No task with ID {task_id} found.")
        sys.exit(1)
    save_tasks(new_tasks)
    print(f"Deleted task {task_id}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simple CLI Todo App with JSON file storage"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # add command
    parser_add = subparsers.add_parser("add", help="Add a new task")
    parser_add.add_argument("description", type=str, help="Task description")

    # list command
    subparsers.add_parser("list", help="List all tasks")

    # complete command
    parser_complete = subparsers.add_parser("complete", help="Mark a task as completed")
    parser_complete.add_argument("id", type=int, help="Task ID to mark complete")

    # delete command
    parser_delete = subparsers.add_parser("delete", help="Delete a task")
    parser_delete.add_argument("id", type=int, help="Task ID to delete")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "add":
        add_task(args.description)
    elif args.command == "list":
        list_tasks()
    elif args.command == "complete":
        complete_task(args.id)
    elif args.command == "delete":
        delete_task(args.id)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()
