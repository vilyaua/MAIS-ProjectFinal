"""Flask REST API for task management with SQLite persistence."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

VALID_PRIORITIES = {"low", "medium", "high"}
DEFAULT_API_KEY = "dev-api-key"


class ValidationError(ValueError):
    """Raised when request input validation fails."""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Validation failed")
        self.errors = errors


def create_app(database_path: str = "tasks.db", seed_default_user: bool = True) -> Flask:
    """Create and configure the Flask application.

    Args:
        database_path: SQLite database file path. Use ":memory:" for tests.
        seed_default_user: When true, inserts a development user with
            ``DEFAULT_API_KEY`` if it does not already exist.

    Returns:
        Configured Flask application.
    """
    app = Flask(__name__)
    app.config["DATABASE"] = database_path
    app.config["JSON_SORT_KEYS"] = False

    with app.app_context():
        init_db(seed_default_user=seed_default_user)

    @app.teardown_appcontext
    def close_db(error: Optional[BaseException]) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> tuple[Any, int]:
        return jsonify({"error": "validation_error", "messages": error.errors}), 400

    @app.errorhandler(sqlite3.Error)
    def handle_database_error(error: sqlite3.Error) -> tuple[Any, int]:
        app.logger.exception("Database error: %s", error)
        return jsonify({"error": "database_error", "message": "A database error occurred."}), 500

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException) -> tuple[Any, int]:
        return jsonify({"error": error.name.lower().replace(" ", "_"), "message": error.description}), error.code or 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> tuple[Any, int]:
        app.logger.exception("Unexpected error: %s", error)
        return jsonify({"error": "internal_server_error", "message": "An unexpected error occurred."}), 500

    @app.post("/tasks")
    @require_api_key
    def create_task() -> tuple[Any, int]:
        payload = get_json_payload()
        validated = validate_task_payload(payload, partial=False)
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO tasks (user_id, title, description, priority, due_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                g.current_user["id"],
                validated["title"],
                validated["description"],
                validated["priority"],
                validated["due_date"],
            ),
        )
        db.commit()
        task = fetch_task_for_user(cursor.lastrowid, g.current_user["id"])
        return jsonify({"message": "Task created successfully.", "task": task}), 201

    @app.get("/tasks")
    @require_api_key
    def list_tasks() -> tuple[Any, int]:
        rows = get_db().execute(
            """
            SELECT id, title, description, priority, due_date, created_at, updated_at
            FROM tasks
            WHERE user_id = ?
            ORDER BY due_date ASC, id ASC
            """,
            (g.current_user["id"],),
        ).fetchall()
        return jsonify({"tasks": [row_to_task(row) for row in rows]}), 200

    @app.get("/tasks/<int:task_id>")
    @require_api_key
    def get_task(task_id: int) -> tuple[Any, int]:
        task = fetch_task_for_user(task_id, g.current_user["id"])
        if task is None:
            return jsonify({"error": "not_found", "message": "Task not found."}), 404
        return jsonify({"task": task}), 200

    @app.route("/tasks/<int:task_id>", methods=["PUT", "PATCH"])
    @require_api_key
    def update_task(task_id: int) -> tuple[Any, int]:
        if fetch_task_for_user(task_id, g.current_user["id"]) is None:
            return jsonify({"error": "not_found", "message": "Task not found."}), 404

        payload = get_json_payload()
        validated = validate_task_payload(payload, partial=True)
        if not validated:
            raise ValidationError({"body": "At least one task field must be provided."})

        assignments = [f"{field} = ?" for field in validated]
        values = list(validated.values())
        assignments.append("updated_at = CURRENT_TIMESTAMP")
        values.extend([task_id, g.current_user["id"]])

        get_db().execute(
            f"UPDATE tasks SET {', '.join(assignments)} WHERE id = ? AND user_id = ?",
            values,
        )
        get_db().commit()
        task = fetch_task_for_user(task_id, g.current_user["id"])
        return jsonify({"message": "Task updated successfully.", "task": task}), 200

    @app.delete("/tasks/<int:task_id>")
    @require_api_key
    def delete_task(task_id: int) -> tuple[Any, int]:
        db = get_db()
        cursor = db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, g.current_user["id"]),
        )
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "not_found", "message": "Task not found."}), 404
        return jsonify({"message": "Task deleted successfully."}), 200

    return app


def get_db() -> sqlite3.Connection:
    """Return the request-local SQLite connection."""
    if "db" not in g:
        database_path = g.get("database_path") or _current_app_database_path()
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        g.db = connection
    return g.db


def _current_app_database_path() -> str:
    from flask import current_app

    return str(current_app.config["DATABASE"])


def init_db(seed_default_user: bool = True) -> None:
    """Create database tables and optionally seed a default API user."""
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            api_key TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high')),
            due_date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """
    )
    if seed_default_user:
        db.execute(
            "INSERT OR IGNORE INTO users (username, api_key) VALUES (?, ?)",
            ("developer", DEFAULT_API_KEY),
        )
    db.commit()


def create_user(username: str, api_key: str) -> int:
    """Create a user and return the new user's ID."""
    cursor = get_db().execute(
        "INSERT INTO users (username, api_key) VALUES (?, ?)",
        (username, api_key),
    )
    get_db().commit()
    return int(cursor.lastrowid)


def require_api_key(view: Callable[..., Any]) -> Callable[..., Any]:
    """Authenticate requests using X-API-Key or Authorization: Bearer headers."""

    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any) -> Any:
        api_key = request.headers.get("X-API-Key")
        authorization = request.headers.get("Authorization", "")
        if not api_key and authorization.startswith("Bearer "):
            api_key = authorization.removeprefix("Bearer ").strip()

        if not api_key:
            return jsonify({"error": "unauthorized", "message": "Missing API key."}), 401

        user = get_db().execute(
            "SELECT id, username, api_key FROM users WHERE api_key = ?",
            (api_key,),
        ).fetchone()
        if user is None:
            return jsonify({"error": "unauthorized", "message": "Invalid API key."}), 401

        g.current_user = user
        return view(*args, **kwargs)

    return wrapped_view


def get_json_payload() -> dict[str, Any]:
    """Return request JSON body or raise a validation error."""
    if not request.is_json:
        raise ValidationError({"body": "Request body must be JSON."})
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError({"body": "JSON body must be an object."})
    return payload


def validate_task_payload(payload: dict[str, Any], partial: bool) -> dict[str, str]:
    """Validate task create/update payloads.

    Args:
        payload: Request JSON body.
        partial: If true, absent fields are allowed for updates.

    Returns:
        Dict containing validated fields.

    Raises:
        ValidationError: If any field is missing or invalid.
    """
    required_fields = {"title", "description", "priority", "due_date"}
    allowed_fields = required_fields
    errors: dict[str, str] = {}
    validated: dict[str, str] = {}

    unknown_fields = set(payload) - allowed_fields
    for field in sorted(unknown_fields):
        errors[field] = "Unknown field."

    for field in sorted(required_fields):
        value = payload.get(field)
        if value is None:
            if not partial:
                errors[field] = "This field is required."
            continue

        if field in {"title", "description"}:
            if not isinstance(value, str):
                errors[field] = "Must be a string."
            elif not value.strip():
                errors[field] = "Must not be empty."
            else:
                validated[field] = value.strip()
        elif field == "priority":
            if not isinstance(value, str):
                errors[field] = "Must be a string."
            elif value.lower() not in VALID_PRIORITIES:
                errors[field] = "Must be one of: low, medium, high."
            else:
                validated[field] = value.lower()
        elif field == "due_date":
            if not isinstance(value, str):
                errors[field] = "Must be a string in YYYY-MM-DD format."
            else:
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    errors[field] = "Must use YYYY-MM-DD format and be a valid date."
                else:
                    validated[field] = value

    if errors:
        raise ValidationError(errors)
    return validated


def fetch_task_for_user(task_id: int, user_id: int) -> Optional[dict[str, Any]]:
    """Fetch a task by ID for a specific user."""
    row = get_db().execute(
        """
        SELECT id, title, description, priority, due_date, created_at, updated_at
        FROM tasks
        WHERE id = ? AND user_id = ?
        """,
        (task_id, user_id),
    ).fetchone()
    if row is None:
        return None
    return row_to_task(row)


def row_to_task(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a database row to an API task dict."""
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "priority": row["priority"],
        "due_date": row["due_date"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


app = create_app()
