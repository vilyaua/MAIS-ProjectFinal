import json
import sys
from typing import List, Dict, Optional

JSON_FILE = 'todos.json'


class TodoItem:
    def __init__(self, task_id: int, description: str, completed: bool = False) -> None:
        self.id = task_id
        self.description = description
        self.completed = completed

    def to_dict(self) -> Dict:
        return {'id': self.id, 'description': self.description, 'completed': self.completed}

    @staticmethod
    def from_dict(data: Dict) -> 'TodoItem':
        return TodoItem(task_id=data['id'], description=data['description'], completed=data.get('completed', False))


class TodoManager:
    def __init__(self, storage_file: str) -> None:
        self.storage_file = storage_file
        self.todos: List[TodoItem] = []
        self.next_id = 1
        self.load()

    def load(self) -> None:
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError('Data is not a list')
                self.todos = [TodoItem.from_dict(item) for item in data]
                self.next_id = max((t.id for t in self.todos), default=0) + 1
        except FileNotFoundError:
            # File missing: start fresh
            self.todos = []
            self.next_id = 1
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error reading storage file: {e}")
            print("Storage file is corrupted or invalid.")
            choice = input("Do you want to reinitialize the todo list? (y/n): ").strip().lower()
            if choice == 'y':
                self.todos = []
                self.next_id = 1
                self.save()  # reset file
            else:
                print("Cannot continue with corrupted data. Exiting.")
                sys.exit(1)

    def save(self) -> None:
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump([todo.to_dict() for todo in self.todos], f, indent=2)
        except IOError as e:
            print(f"Error writing to storage file: {e}")
            sys.exit(1)

    def add(self, description: str) -> None:
        description = description.strip()
        if not description:
            print("Error: Task description cannot be empty.")
            return
        new_todo = TodoItem(self.next_id, description)
        self.todos.append(new_todo)
        self.next_id += 1
        self.save()
        print(f"Added task {new_todo.id}: {new_todo.description}")

    def list(self) -> None:
        if not self.todos:
            print("No todo tasks found.")
            return
        for todo in self.todos:
            status = 'Completed' if todo.completed else 'Pending'
            print(f"[{todo.id}] {todo.description} - {status}")

    def complete(self, task_id: int) -> None:
        todo = self.find_by_id(task_id)
        if todo:
            if todo.completed:
                print(f"Task {task_id} is already completed.")
                return
            todo.completed = True
            self.save()
            print(f"Task {task_id} marked as completed.")
        else:
            print(f"Error: No task found with ID {task_id}.")

    def delete(self, task_id: int) -> None:
        todo = self.find_by_id(task_id)
        if todo:
            self.todos = [t for t in self.todos if t.id != task_id]
            self.save()
            print(f"Task {task_id} deleted.")
        else:
            print(f"Error: No task found with ID {task_id}.")

    def find_by_id(self, task_id: int) -> Optional[TodoItem]:
        for todo in self.todos:
            if todo.id == task_id:
                return todo
        return None


def print_help() -> None:
    help_text = '''
Todo CLI Application

Commands:
  add "task description"  Add a new todo task
  list                    List all todo tasks
  complete <task_id>      Mark a task as completed
  delete <task_id>        Delete a task
  help                    Show this help message
'''
    print(help_text)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Error: No command provided.")
        print_help()
        sys.exit(1)

    command = args[0].lower()
    manager = TodoManager(JSON_FILE)

    if command == 'add':
        if len(args) < 2:
            print("Error: Missing task description for 'add' command.")
            sys.exit(1)
        # Join all arguments after 'add' as description (to support spaces and quotes)
        description = ' '.join(args[1:]).strip('"')
        manager.add(description)

    elif command == 'list':
        manager.list()

    elif command == 'complete':
        if len(args) != 2:
            print("Error: 'complete' command requires exactly one task ID.")
            sys.exit(1)
        try:
            task_id = int(args[1])
        except ValueError:
            print("Error: Task ID must be an integer.")
            sys.exit(1)
        manager.complete(task_id)

    elif command == 'delete':
        if len(args) != 2:
            print("Error: 'delete' command requires exactly one task ID.")
            sys.exit(1)
        try:
            task_id = int(args[1])
        except ValueError:
            print("Error: Task ID must be an integer.")
            sys.exit(1)
        manager.delete(task_id)

    elif command == 'help':
        print_help()

    else:
        print(f"Error: Unknown command '{command}'.")
        print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
