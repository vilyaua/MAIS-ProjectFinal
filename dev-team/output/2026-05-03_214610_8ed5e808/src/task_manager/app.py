"""Flask REST API for authenticated task management."""

from __future__ import annotations

import re
import sqlite3
from datetime import date
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

from flask import Flask, Response, g, jsonify, request

TaskRoute = TypeVar("TaskRoute", bound=Callable[..., tuple[Response, int] | Response])

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VALID_PRIORITIES = {1, 2, 3, 4, 5}
REQUIRED_TASK_FIELDS = {"title", "description", "priority", "due_date"}


class ValidationError(ValueError):
    """Raised when request data is invalid."""


class NotFoundError(LookupError):
    """Raised when a requested resource does not exist for the user."""


def create_app(database_path: str | None = None, testing: bool = False) -> Flask:
    """Create and configure the Flask application.

    Args:
        database_path: Path to the SQLite database file. ``None`` uses
            ``task_manager.sqlite3`` in the current working directory.
        testing: Whether to enable Flask testing mode.

    Returns:
        A configured Flask application.
    """
    app = Flask(__name__)
    app.config["TESTING"] = testing
    app.config["DATABASE"] = database_path or "task_manager.sqlite3"

    with app.app_context():
        init_db()

    @app.teardown_appcontext
    def close_connection(_exception: BaseException | None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
        return json_error(str(error), 400)

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error: NotFoundError) -> tuple[Response, int]:
        return json_error(str(error), 404)

    @app.errorhandler(sqlite3.Error)
    def handle_database_error(error: sqlite3.Error) -> tuple[Response, int]:
        app.logger.exception("Database error: %s", error)
        return json_error("Database error occurred while processing request", 500)

    @app.errorhandler(404)
    def handle_404(_error: Exception) -> tuple[Response, int]:
        return json_error("Endpoint not found", 404)

    @app.route("/tasks", methods=["POST"])
    @require_api_key
    def create_task() -> tuple[Response, int]:
        payload = get_json_payload()
        task_data = validate_task_payload(payload, require_all=True)
        task = insert_task(cast(int, g.current_user_id), task_data)
        return jsonify(task), 201

    @app.route("/tasks", methods=["GET"])
    @require_api_key
    def list_tasks() -> Response:
        tasks = fetch_tasks(cast(int, g.current_user_id))
        return jsonify({"tasks": tasks})

    @app.route("/tasks/<int:task_id>", methods=["GET"])
    @require_api_key
    def get_task(task_id: int) -> Response:
        task = fetch_task(cast(int, g.current_user_id), task_id)
        if task is None:
            raise NotFoundError("Task not found")
        return jsonify(task)

    @app.route("/tasks/<int:task_id>", methods=["PUT"])
    @require_api_key
    def update_task(task_id: int) -> Response:
        payload = get_json_payload()
        task_data = validate_task_payload(payload, require_all=False)
        task = update_existing_task(cast(int, g.current_user_id), task_id, task_data)
        return jsonify(task)

    @app.route("/tasks/<int:task_id>", methods=["DELETE"])
    @require_api_key
    def delete_task(task_id: int) -> tuple[str, int]:
        delete_existing_task(cast(int, g.current_user_id), task_id)
        return "", 204

    @app.route("/users", methods=["POST"])
    def create_user() -> tuple[Response, int]:
        """Create a user and API key.

        This bootstrap endpoint makes the API usable without direct database
        access. It is intentionally unauthenticated because it creates the
        credential used to call all task endpoints.
        """
        payload = get_json_payload()
        username = payload.get("username")
        api_key = payload.get("api_key")
        if not isinstance(username, str) or not username.strip():
            raise ValidationError("Field 'username' is required and must be a non-empty string")
        if api_key is not None and (not isinstance(api_key, str) or not api_key.strip()):
            raise ValidationError("Field 'api_key' must be a non-empty string when provided")
        user = insert_user(username.strip(), api_key.strip() if isinstance(api_key, str) else None)
        return jsonify(user), 201

    return app


def get_db() -> sqlite3.Connection:
    """Return a request-local SQLite connection."""
    if "db" not in g:
        database = Path(cast(str, current_app_config("DATABASE")))
        if database != Path(":memory:"):
            database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return cast(sqlite3.Connection, g.db)


def current_app_config(key: str) -> Any:
    """Read Flask current app config without importing current_app globally."""
    from flask import current_app

    return current_app.config[key]


def init_db() -> None:
    """Create database tables when they do not exist."""
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 5),
            due_date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """
    )
    db.commit()


def json_error(message: str, status_code: int) -> tuple[Response, int]:
    """Return a standardized JSON error response."""
    return jsonify({"error": message}), status_code


def extract_api_key() -> str | None:
    """Extract an API key from supported request headers."""
    header_key = request.headers.get("X-API-Key")
    if header_key:
        return header_key.strip()

    authorization = request.headers.get("Authorization")
    if not authorization:
        return None

    parts = authorization.split(maxsplit=1)
    if len(parts) == 2 and parts[0].lower() in {"bearer", "apikey"}:
        return parts[1].strip()
    return None


def require_api_key(route: TaskRoute) -> TaskRoute:
    """Authenticate a route using an API key."""

    @wraps(route)
    def wrapper(*args: Any, **kwargs: Any) -> tuple[Response, int] | Response:
        api_key = extract_api_key()
        if not api_key:
            return json_error("Missing API key", 401)

        row = (
            get_db()
            .execute(
                """
            SELECT users.id AS user_id
            FROM api_keys
            JOIN users ON users.id = api_keys.user_id
            WHERE api_keys.key = ?
            """,
                (api_key,),
            )
            .fetchone()
        )
        if row is None:
            return json_error("Invalid API key", 401)

        g.current_user_id = int(row["user_id"])
        return route(*args, **kwargs)

    return cast(TaskRoute, wrapper)


def get_json_payload() -> dict[str, Any]:
    """Return JSON request data or raise a 400 validation error."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")
    return payload


def validate_task_payload(payload: dict[str, Any], require_all: bool) -> dict[str, Any]:
    """Validate create/update task payloads.

    Args:
        payload: JSON object from the request body.
        require_all: If true, all task fields are required. If false, at
            least one task field must be present.

    Returns:
        Sanitized field values ready for persistence.
    """
    allowed_fields = REQUIRED_TASK_FIELDS
    unknown_fields = set(payload) - allowed_fields
    if unknown_fields:
        fields = ", ".join(sorted(unknown_fields))
        raise ValidationError(f"Unknown field(s): {fields}")

    if require_all:
        missing_fields = allowed_fields - set(payload)
        if missing_fields:
            fields = ", ".join(sorted(missing_fields))
            raise ValidationError(f"Missing required field(s): {fields}")
    elif not any(field in payload for field in allowed_fields):
        raise ValidationError("At least one task field must be provided")

    cleaned: dict[str, Any] = {}
    if "title" in payload:
        cleaned["title"] = validate_non_empty_string(payload["title"], "title")
    if "description" in payload:
        cleaned["description"] = validate_non_empty_string(payload["description"], "description")
    if "priority" in payload:
        cleaned["priority"] = validate_priority(payload["priority"])
    if "due_date" in payload:
        cleaned["due_date"] = validate_due_date(payload["due_date"])
    return cleaned


def validate_non_empty_string(value: Any, field_name: str) -> str:
    """Validate a non-empty string field."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"Field '{field_name}' must be a non-empty string")
    return value.strip()


def validate_priority(value: Any) -> int:
    """Validate task priority, accepted as an integer from 1 through 5."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError("Field 'priority' must be an integer from 1 to 5")
    if value not in VALID_PRIORITIES:
        raise ValidationError("Field 'priority' must be between 1 and 5")
    return value


def validate_due_date(value: Any) -> str:
    """Validate due date in YYYY-MM-DD format."""
    if not isinstance(value, str) or not DATE_PATTERN.match(value):
        raise ValidationError("Field 'due_date' must use YYYY-MM-DD format")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError("Field 'due_date' must be a valid calendar date") from exc
    return value


def row_to_task(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a SQLite row to an API task object."""
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "priority": row["priority"],
        "due_date": row["due_date"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def insert_user(username: str, api_key: str | None) -> dict[str, Any]:
    """Create a user and API key."""
    import secrets

    key = api_key or secrets.token_urlsafe(32)
    db = get_db()
    try:
        cursor = db.execute("INSERT INTO users (username) VALUES (?)", (username,))
        user_id = int(cursor.lastrowid)
        db.execute("INSERT INTO api_keys (user_id, key) VALUES (?, ?)", (user_id, key))
        db.commit()
    except sqlite3.IntegrityError as exc:
        db.rollback()
        raise ValidationError("Username or API key already exists") from exc
    return {"id": user_id, "username": username, "api_key": key}


def insert_task(user_id: int, task_data: dict[str, Any]) -> dict[str, Any]:
    """Insert a new task for a user and return it."""
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO tasks (user_id, title, description, priority, due_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            task_data["title"],
            task_data["description"],
            task_data["priority"],
            task_data["due_date"],
        ),
    )
    db.commit()
    task = fetch_task(user_id, int(cursor.lastrowid))
    if task is None:
        raise sqlite3.DatabaseError("Inserted task could not be fetched")
    return task


def fetch_tasks(user_id: int) -> list[dict[str, Any]]:
    """Fetch all tasks for a user."""
    rows = (
        get_db()
        .execute(
            """
        SELECT id, title, description, priority, due_date, created_at, updated_at
        FROM tasks
        WHERE user_id = ?
        ORDER BY id
        """,
            (user_id,),
        )
        .fetchall()
    )
    return [row_to_task(row) for row in rows]


def fetch_task(user_id: int, task_id: int) -> dict[str, Any] | None:
    """Fetch one task belonging to a user."""
    row = (
        get_db()
        .execute(
            """
        SELECT id, title, description, priority, due_date, created_at, updated_at
        FROM tasks
        WHERE user_id = ? AND id = ?
        """,
            (user_id, task_id),
        )
        .fetchone()
    )
    return row_to_task(row) if row is not None else None


def update_existing_task(user_id: int, task_id: int, task_data: dict[str, Any]) -> dict[str, Any]:
    """Update a task belonging to a user and return the updated task."""
    if fetch_task(user_id, task_id) is None:
        raise NotFoundError("Task not found")

    assignments = [f"{field} = ?" for field in task_data]
    values = list(task_data.values())
    assignments.append("updated_at = CURRENT_TIMESTAMP")
    values.extend([user_id, task_id])

    get_db().execute(
        f"UPDATE tasks SET {', '.join(assignments)} WHERE user_id = ? AND id = ?",
        values,
    )
    get_db().commit()
    updated_task = fetch_task(user_id, task_id)
    if updated_task is None:
        raise sqlite3.DatabaseError("Updated task could not be fetched")
    return updated_task


def delete_existing_task(user_id: int, task_id: int) -> None:
    """Delete a task belonging to a user."""
    cursor = get_db().execute(
        "DELETE FROM tasks WHERE user_id = ? AND id = ?",
        (user_id, task_id),
    )
    get_db().commit()
    if cursor.rowcount == 0:
        raise NotFoundError("Task not found")


if __name__ == "__main__":
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=True)
