import json
import sys
from typing import List, Dict, Any

TODO_FILE = 'todo_tasks.json'


def load_tasks() -> List[Dict[str, Any]]:
    """Load tasks from the JSON file, return empty list if file not found."""
    try:
        with open(TODO_FILE, 'r', encoding='utf-8') as file:
            tasks = json.load(file)
            if not isinstance(tasks, list):
                print(f'Error: JSON format invalid - expected a list of tasks.')
                sys.exit(1)
            # Validate each task
            for task in tasks:
                if not isinstance(task, dict):
                    print(f'Error: JSON format invalid - each task should be an object.')
                    sys.exit(1)
                if 'id' not in task or 'description' not in task or 'completed' not in task:
                    print(f'Error: JSON format invalid - missing fields in a task.')
                    sys.exit(1)
                if not isinstance(task['id'], int) or not isinstance(task['description'], str) or not isinstance(task['completed'], bool):
                    print(f'Error: JSON format invalid - incorrect field types in a task.')
                    sys.exit(1)
            return tasks
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f'Error: Corrupted JSON file. Could not parse {TODO_FILE}.')
        sys.exit(1)
    except Exception as e:
        print(f'Error: Unexpected error while reading {TODO_FILE}: {e}')
        sys.exit(1)


def save_tasks(tasks: List[Dict[str, Any]]) -> None:
    """Save tasks to the JSON file."""
    try:
        with open(TODO_FILE, 'w', encoding='utf-8') as file:
            json.dump(tasks, file, indent=4)
    except Exception as e:
        print(f'Error: Failed to write to {TODO_FILE}: {e}')
        sys.exit(1)


def add_task(description: str) -> None:
    description = description.strip()
    if not description:
        print('Error: Task description cannot be empty.')
        sys.exit(1)

    tasks = load_tasks()
    new_id = max((task['id'] for task in tasks), default=0) + 1
    new_task = {
        'id': new_id,
        'description': description,
        'completed': False
    }
    tasks.append(new_task)
    save_tasks(tasks)
    print(f'Task added with ID {new_id}.')


def list_tasks() -> None:
    tasks = load_tasks()
    if not tasks:
        print('No tasks found.')
        return

    for task in tasks:
        status = 'Done' if task['completed'] else 'Pending'
        print(f'{task["id"]}: {task["description"]} [{status}]')


def complete_task(task_id: str) -> None:
    try:
        id_int = int(task_id)
    except ValueError:
        print('Error: Task ID must be a valid integer.')
        sys.exit(1)

    tasks = load_tasks()
    found = False
    for task in tasks:
        if task['id'] == id_int:
            if task['completed']:
                print(f'Task {id_int} is already completed.')
                sys.exit(0)
            task['completed'] = True
            found = True
            break

    if not found:
        print(f'Error: Task with ID {id_int} not found.')
        sys.exit(1)

    save_tasks(tasks)
    print(f'Task {id_int} marked as completed.')


def delete_task(task_id: str) -> None:
    try:
        id_int = int(task_id)
    except ValueError:
        print('Error: Task ID must be a valid integer.')
        sys.exit(1)

    tasks = load_tasks()
    new_tasks = [task for task in tasks if task['id'] != id_int]

    if len(new_tasks) == len(tasks):
        print(f'Error: Task with ID {id_int} not found.')
        sys.exit(1)

    save_tasks(new_tasks)
    print(f'Task {id_int} deleted.')


def print_help() -> None:
    print("""
To-Do CLI usage:
  add <task_description>    Add a new task (description cannot be empty)
  list                      List all tasks with their status and IDs
  complete <task_id>        Mark the task with the given ID as completed
  delete <task_id>          Delete the task with the given ID
  help                      Show this help message
""")


def main() -> None:
    if len(sys.argv) < 2:
        print('Error: No command provided.')
        print_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'add':
        if len(sys.argv) < 3:
            print('Error: Missing task description for add command.')
            sys.exit(1)
        description = ' '.join(sys.argv[2:])
        add_task(description)

    elif command == 'list':
        list_tasks()

    elif command == 'complete':
        if len(sys.argv) < 3:
            print('Error: Missing task ID for complete command.')
            sys.exit(1)
        complete_task(sys.argv[2])

    elif command == 'delete':
        if len(sys.argv) < 3:
            print('Error: Missing task ID for delete command.')
            sys.exit(1)
        delete_task(sys.argv[2])

    elif command == 'help':
        print_help()

    else:
        print(f'Error: Unknown command "{command}".')
        print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
