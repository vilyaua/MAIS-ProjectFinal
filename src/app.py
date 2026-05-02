"""Flask REST API for a SQLite-backed task manager."""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Response

DATABASE_PATH = Path(__file__).resolve().parent.parent / "tasks.db"
API_KEY_HEADER = "X-API-Key"
DEFAULT_API_KEYS = {"test-api-key"}
ALLOWED_PRIORITIES = range(1, 6)
ALLOWED_STATUSES = {"pending", "in_progress", "completed"}
DATE_FORMAT = "%Y-%m-%d"

F = TypeVar("F", bound=Callable[..., Any])


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=str(DATABASE_PATH),
        API_KEYS=set(
            key.strip()
            for key in os.environ.get("TASK_API_KEYS", "test-api-key").split(",")
            if key.strip()
        )
        or DEFAULT_API_KEYS,
        TESTING=False,
    )

    if test_config:
        app.config.update(test_config)

    register_error_handlers(app)
    register_routes(app)

    with app.app_context():
        init_db()

    return app


def get_db() -> sqlite3.Connection:
    """Return a request-scoped SQLite connection."""
    if "db" not in g:
        database = str(g.current_app.config["DATABASE"]) if hasattr(g, "current_app") else None
        if database is None:
            from flask import current_app

            database = str(current_app.config["DATABASE"])
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        g.db = connection
    return cast(sqlite3.Connection, g.db)


def close_db(_error: Exception | None = None) -> None:
    """Close the request-scoped database connection, if it exists."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Create required database tables if they do not already exist."""
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            priority INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    db.commit()


def register_error_handlers(app: Flask) -> None:
    """Register JSON error handlers and teardown callbacks."""
    app.teardown_appcontext(close_db)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException) -> tuple[Response, int]:
        response = jsonify({"error": error.name, "message": error.description})
        return response, error.code or 500

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception) -> tuple[Response, int]:
        if app.config.get("TESTING"):
            raise error
        response = jsonify(
            {"error": "Internal Server Error", "message": "An unexpected error occurred."}
        )
        return response, 500


def require_api_key(function: F) -> F:
    """Require a valid API key in the configured request header."""

    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        from flask import current_app

        api_key = request.headers.get(API_KEY_HEADER)
        valid_keys = set(current_app.config.get("API_KEYS", DEFAULT_API_KEYS))
        if not api_key:
            return (
                jsonify(
                    {
                        "error": "Unauthorized",
                        "message": f"Missing API key. Provide it in the {API_KEY_HEADER} header.",
                    }
                ),
                401,
            )
        if api_key not in valid_keys:
            return (
                jsonify({"error": "Unauthorized", "message": "Invalid API key."}),
                401,
            )
        return function(*args, **kwargs)

    return cast(F, wrapper)


def parse_due_date(value: Any, *, require_future: bool = True) -> date:
    """Parse and validate a due date value."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("due_date must be a non-empty string in YYYY-MM-DD format.")
    try:
        parsed = datetime.strptime(value.strip(), DATE_FORMAT).date()
    except ValueError as exc:
        raise ValueError("due_date must be a valid date in YYYY-MM-DD format.") from exc
    if require_future and parsed <= date.today():
        raise ValueError("due_date must be a future date.")
    return parsed


def validate_task_payload(data: Any, *, partial: bool = False) -> dict[str, Any]:
    """Validate task creation/update payload and return normalized values."""
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")

    required_fields = {"description", "priority", "due_date", "status"}
    if not partial:
        missing = sorted(field for field in required_fields if field not in data)
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(missing)}.")

    allowed_fields = required_fields
    unknown = sorted(field for field in data if field not in allowed_fields)
    if unknown:
        raise ValueError(f"Unknown field(s): {', '.join(unknown)}.")

    validated: dict[str, Any] = {}

    if "description" in data:
        description = data["description"]
        if not isinstance(description, str) or not description.strip():
            raise ValueError("description must be a non-empty string.")
        validated["description"] = description.strip()

    if "priority" in data:
        priority = data["priority"]
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise ValueError("priority must be an integer between 1 and 5.")
        if priority not in ALLOWED_PRIORITIES:
            raise ValueError("priority must be between 1 and 5.")
        validated["priority"] = priority

    if "due_date" in data:
        validated["due_date"] = parse_due_date(data["due_date"]).isoformat()

    if "status" in data:
        status = data["status"]
        if not isinstance(status, str) or status not in ALLOWED_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_STATUSES))
            raise ValueError(f"status must be one of: {allowed}.")
        validated["status"] = status

    if partial and not validated:
        raise ValueError("At least one updatable field must be provided.")

    return validated


def row_to_task(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a SQLite row to an API task representation."""
    return {
        "id": row["id"],
        "description": row["description"],
        "priority": row["priority"],
        "due_date": row["due_date"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def bad_request(message: str) -> tuple[Response, int]:
    """Return a standardized 400 response."""
    return jsonify({"error": "Bad Request", "message": message}), 400


def get_task_or_404(task_id: int) -> sqlite3.Row | None:
    """Fetch a task by id."""
    return get_db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def register_routes(app: Flask) -> None:
    """Register task API routes."""

    @app.get("/health")
    def health() -> tuple[Response, int]:
        return jsonify({"status": "ok"}), 200

    @app.post("/tasks")
    @require_api_key
    def create_task() -> tuple[Response, int]:
        data = request.get_json(silent=True)
        try:
            task = validate_task_payload(data)
        except ValueError as exc:
            return bad_request(str(exc))

        timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO tasks (description, priority, due_date, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task["description"],
                task["priority"],
                task["due_date"],
                task["status"],
                timestamp,
                timestamp,
            ),
        )
        db.commit()
        row = get_task_or_404(int(cursor.lastrowid))
        return jsonify(row_to_task(cast(sqlite3.Row, row))), 201

    @app.get("/tasks")
    @require_api_key
    def list_tasks() -> tuple[Response, int]:
        clauses: list[str] = []
        params: list[Any] = []

        priority_filter = request.args.get("priority")
        if priority_filter is not None:
            try:
                priority = int(priority_filter)
            except ValueError:
                return bad_request("priority filter must be an integer between 1 and 5.")
            if priority not in ALLOWED_PRIORITIES:
                return bad_request("priority filter must be between 1 and 5.")
            clauses.append("priority = ?")
            params.append(priority)

        due_date_filter = request.args.get("due_date")
        if due_date_filter is not None:
            try:
                parsed_due_date = parse_due_date(due_date_filter, require_future=False)
            except ValueError as exc:
                return bad_request(str(exc))
            clauses.append("due_date = ?")
            params.append(parsed_due_date.isoformat())

        query = "SELECT * FROM tasks"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id ASC"

        rows = get_db().execute(query, params).fetchall()
        return jsonify({"tasks": [row_to_task(row) for row in rows]}), 200

    @app.get("/tasks/<int:task_id>")
    @require_api_key
    def get_task(task_id: int) -> tuple[Response, int]:
        row = get_task_or_404(task_id)
        if row is None:
            return jsonify({"error": "Not Found", "message": "Task not found."}), 404
        return jsonify(row_to_task(row)), 200

    @app.put("/tasks/<int:task_id>")
    @require_api_key
    def update_task(task_id: int) -> tuple[Response, int]:
        existing = get_task_or_404(task_id)
        if existing is None:
            return jsonify({"error": "Not Found", "message": "Task not found."}), 404

        data = request.get_json(silent=True)
        try:
            updates = validate_task_payload(data, partial=True)
        except ValueError as exc:
            return bad_request(str(exc))

        timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        updates["updated_at"] = timestamp
        assignments = ", ".join(f"{field} = ?" for field in updates)
        values = list(updates.values()) + [task_id]
        db = get_db()
        db.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", values)
        db.commit()

        row = get_task_or_404(task_id)
        return jsonify(row_to_task(cast(sqlite3.Row, row))), 200

    @app.delete("/tasks/<int:task_id>")
    @require_api_key
    def delete_task(task_id: int) -> tuple[Response, int]:
        db = get_db()
        cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Not Found", "message": "Task not found."}), 404
        return jsonify({"message": "Task deleted."}), 200


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
