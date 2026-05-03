"""Task Manager REST API implemented with Flask and SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

from flask import Flask, Response, current_app, g, jsonify, request

VALID_PRIORITIES = {"low", "medium", "high"}
DEFAULT_API_KEYS = {"secret-api-key"}

F = TypeVar("F", bound=Callable[..., Any])


class ValidationError(ValueError):
    """Raised when request JSON fails task validation."""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Invalid task input")
        self.errors = errors


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=str(Path(__file__).resolve().parent.parent / "tasks.sqlite3"),
        API_KEYS=DEFAULT_API_KEYS,
    )

    if test_config:
        app.config.update(test_config)

    @app.before_request
    def ensure_database() -> None:
        init_db()

    @app.teardown_appcontext
    def close_db_connection(_exception: BaseException | None) -> None:
        close_db()

    register_routes(app)
    register_error_handlers(app)
    return app


def get_db() -> sqlite3.Connection:
    """Return a request-scoped SQLite connection."""
    if "db" not in g:
        database = current_app.config["DATABASE"]
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        g.db = connection
    return cast(sqlite3.Connection, g.db)


def close_db() -> None:
    """Close the request-scoped SQLite connection, if present."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Create the tasks table if it does not already exist."""
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            due_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    db.commit()


def require_api_key(view: F) -> F:
    """Require a valid API key in the X-API-Key header or api_key query param."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        supplied_key = request.headers.get("X-API-Key") or request.args.get("api_key")
        valid_keys = set(current_app.config.get("API_KEYS", set()))
        if not supplied_key or supplied_key not in valid_keys:
            return jsonify({"error": "Unauthorized", "message": "Invalid or missing API key"}), 401
        return view(*args, **kwargs)

    return cast(F, wrapped)


def validate_task_payload(data: Any, *, partial: bool = False) -> dict[str, str]:
    """Validate a JSON payload for task creation or update."""
    if not isinstance(data, dict):
        raise ValidationError({"body": "Request body must be a JSON object"})

    errors: dict[str, str] = {}
    required_fields = ("title", "description", "priority", "due_date")
    allowed_fields = set(required_fields)

    unknown_fields = sorted(set(data) - allowed_fields)
    if unknown_fields:
        errors["unknown_fields"] = f"Unsupported fields: {', '.join(unknown_fields)}"

    if not partial:
        for field in required_fields:
            if field not in data:
                errors[field] = "This field is required"

    cleaned: dict[str, str] = {}

    for field in ("title", "description"):
        if field in data:
            value = data[field]
            if not isinstance(value, str) or not value.strip():
                errors[field] = "Must be a non-empty string"
            else:
                cleaned[field] = value.strip()

    if "priority" in data:
        priority = data["priority"]
        if not isinstance(priority, str) or priority.lower() not in VALID_PRIORITIES:
            errors["priority"] = "Must be one of: low, medium, high"
        else:
            cleaned["priority"] = priority.lower()

    if "due_date" in data:
        due_date = data["due_date"]
        if not isinstance(due_date, str):
            errors["due_date"] = "Must be a date string in YYYY-MM-DD format"
        else:
            try:
                parsed = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                errors["due_date"] = "Must be a valid date in YYYY-MM-DD format"
            else:
                cleaned["due_date"] = parsed.date().isoformat()

    if partial and not cleaned and not errors:
        errors["body"] = "At least one task field must be provided"

    if errors:
        raise ValidationError(errors)

    return cleaned


def row_to_task(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a SQLite row to a JSON-serializable task dictionary."""
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "priority": row["priority"],
        "due_date": row["due_date"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_task_or_404(task_id: int) -> sqlite3.Row | tuple[Response, int]:
    """Fetch a task row by ID or return a Flask 404 response tuple."""
    row = get_db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404
    return row


def register_routes(app: Flask) -> None:
    """Register REST API routes on the Flask app."""

    @app.get("/health")
    @require_api_key
    def health() -> Response:
        return jsonify({"status": "ok"})

    @app.post("/tasks")
    @require_api_key
    def create_task() -> tuple[Response, int]:
        payload = validate_task_payload(request.get_json(silent=True), partial=False)
        now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO tasks (title, description, priority, due_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload["title"],
                payload["description"],
                payload["priority"],
                payload["due_date"],
                now,
                now,
            ),
        )
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return jsonify(row_to_task(row)), 201

    @app.get("/tasks")
    @require_api_key
    def list_tasks() -> Response:
        rows = get_db().execute("SELECT * FROM tasks ORDER BY id ASC").fetchall()
        return jsonify({"tasks": [row_to_task(row) for row in rows]})

    @app.get("/tasks/<int:task_id>")
    @require_api_key
    def get_task(task_id: int) -> Response | tuple[Response, int]:
        row = get_task_or_404(task_id)
        if isinstance(row, tuple):
            return row
        return jsonify(row_to_task(row))

    @app.put("/tasks/<int:task_id>")
    @require_api_key
    def update_task(task_id: int) -> Response | tuple[Response, int]:
        existing = get_task_or_404(task_id)
        if isinstance(existing, tuple):
            return existing

        payload = validate_task_payload(request.get_json(silent=True), partial=True)
        fields = []
        values: list[str | int] = []
        for field in ("title", "description", "priority", "due_date"):
            if field in payload:
                fields.append(f"{field} = ?")
                values.append(payload[field])
        now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        fields.append("updated_at = ?")
        values.append(now)
        values.append(task_id)

        db = get_db()
        db.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", tuple(values))
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return jsonify(row_to_task(row))

    @app.delete("/tasks/<int:task_id>")
    @require_api_key
    def delete_task(task_id: int) -> tuple[str, int] | tuple[Response, int]:
        existing = get_task_or_404(task_id)
        if isinstance(existing, tuple):
            return existing
        db = get_db()
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db.commit()
        return "", 204


def register_error_handlers(app: Flask) -> None:
    """Register JSON error handlers."""

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
        return jsonify({"error": "Bad Request", "details": error.errors}), 400

    @app.errorhandler(404)
    def handle_not_found(_error: Exception) -> tuple[Response, int]:
        return jsonify({"error": "Not Found", "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_error: Exception) -> tuple[Response, int]:
        return jsonify({"error": "Method Not Allowed"}), 405


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
