"""Flask REST API for task management with SQLite persistence."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from flask import Flask, g, jsonify, request

DATE_FORMAT = "%Y-%m-%d"
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_API_KEY = "test-api-key"


class ValidationError(ValueError):
    """Raised when request data fails validation."""


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get("TASK_API_DATABASE", "tasks.db"),
        DEFAULT_API_KEY=os.environ.get("TASK_API_KEY", DEFAULT_API_KEY),
    )

    if test_config:
        app.config.update(test_config)

    app.teardown_appcontext(close_db)
    register_routes(app)

    with app.app_context():
        init_db()

    return app


def get_db() -> sqlite3.Connection:
    """Return a SQLite connection.

    File-backed databases use a request-scoped connection. The special
    ``:memory:`` database is kept application-scoped so schema/data survive
    across Flask test-client requests.
    """
    from flask import current_app

    database = app_database_path()
    if database == ":memory:":
        conn = current_app.config.get("_MEMORY_DB_CONN")
        if conn is None:
            conn = sqlite3.connect(database)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            current_app.config["_MEMORY_DB_CONN"] = conn
        return conn

    if "db" not in g:
        Path(database).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def app_database_path() -> str:
    """Get database path from current Flask app configuration."""
    from flask import current_app

    return str(current_app.config["DATABASE"])


def close_db(_error: Optional[BaseException] = None) -> None:
    """Close the request-scoped database connection if present."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Create database tables and ensure the default API user exists."""
    from flask import current_app

    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            api_key TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            priority INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """
    )
    default_key = current_app.config["DEFAULT_API_KEY"]
    db.execute(
        "INSERT OR IGNORE INTO users (name, api_key) VALUES (?, ?)",
        ("Default User", default_key),
    )
    db.commit()


def get_api_key() -> Optional[str]:
    """Extract the API key from supported request headers."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key.strip()

    auth_header = request.headers.get("Authorization", "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None


def authenticate() -> Tuple[Optional[sqlite3.Row], Optional[Tuple[Any, int]]]:
    """Authenticate the request by API key."""
    api_key = get_api_key()
    if not api_key:
        return None, error_response("Missing API key", 401)

    user = (
        get_db()
        .execute("SELECT id, name, api_key FROM users WHERE api_key = ?", (api_key,))
        .fetchone()
    )
    if user is None:
        return None, error_response("Invalid API key", 401)
    return user, None


def require_json_body() -> Dict[str, Any]:
    """Return JSON body or raise a validation error."""
    if not request.is_json:
        raise ValidationError("Request body must be JSON")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    return data


def parse_due_date(value: Any) -> str:
    """Validate and normalize a due date value as YYYY-MM-DD."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("due_date is required and must be a date string")
    try:
        parsed = datetime.strptime(value.strip(), DATE_FORMAT).date()
    except ValueError as exc:
        raise ValidationError("due_date must use YYYY-MM-DD format") from exc
    return parsed.isoformat()


def parse_priority(value: Any) -> int:
    """Validate and normalize priority."""
    if isinstance(value, bool):
        raise ValidationError("priority must be an integer")
    try:
        priority = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("priority must be an integer") from exc
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError(f"priority must be between {MIN_PRIORITY} and {MAX_PRIORITY}")
    return priority


def validate_task_payload(data: Dict[str, Any], partial: bool = False) -> Dict[str, Any]:
    """Validate task creation/update payload."""
    allowed_fields = {"title", "description", "priority", "due_date"}
    unknown_fields = sorted(set(data) - allowed_fields)
    if unknown_fields:
        raise ValidationError(f"Unknown field(s): {', '.join(unknown_fields)}")

    required_fields = {"title", "priority", "due_date"}
    if not partial:
        missing = sorted(field for field in required_fields if field not in data)
        if missing:
            raise ValidationError(f"Missing required field(s): {', '.join(missing)}")
    elif not data:
        raise ValidationError("At least one task field must be provided")

    validated: Dict[str, Any] = {}
    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            raise ValidationError("title is required and must be a non-empty string")
        validated["title"] = data["title"].strip()

    if "description" in data:
        if data["description"] is None:
            validated["description"] = ""
        elif not isinstance(data["description"], str):
            raise ValidationError("description must be a string")
        else:
            validated["description"] = data["description"].strip()
    elif not partial:
        validated["description"] = ""

    if "priority" in data:
        validated["priority"] = parse_priority(data["priority"])

    if "due_date" in data:
        validated["due_date"] = parse_due_date(data["due_date"])

    return validated


def task_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a task row to a JSON-serializable dict."""
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "priority": row["priority"],
        "due_date": row["due_date"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def error_response(message: str, status_code: int) -> Tuple[Any, int]:
    """Create a consistent JSON error response."""
    return jsonify({"error": message}), status_code


def register_routes(app: Flask) -> None:
    """Register all API routes."""

    @app.errorhandler(404)
    def handle_404(_error: Exception) -> Tuple[Any, int]:
        return error_response("Resource not found", 404)

    @app.errorhandler(405)
    def handle_405(_error: Exception) -> Tuple[Any, int]:
        return error_response("Method not allowed", 405)

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> Tuple[Any, int]:
        return error_response(str(error), 400)

    @app.get("/health")
    def health() -> Tuple[Any, int]:
        return jsonify({"status": "ok"}), 200

    @app.post("/tasks")
    def create_task() -> Tuple[Any, int]:
        user, auth_error = authenticate()
        if auth_error:
            return auth_error
        assert user is not None

        payload = validate_task_payload(require_json_body())
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO tasks (user_id, title, description, priority, due_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                payload["title"],
                payload["description"],
                payload["priority"],
                payload["due_date"],
            ),
        )
        db.commit()
        task = fetch_task(cursor.lastrowid, user["id"])
        return jsonify({"task": task_to_dict(task)}), 201

    @app.get("/tasks")
    def list_tasks() -> Tuple[Any, int]:
        user, auth_error = authenticate()
        if auth_error:
            return auth_error
        assert user is not None

        sql = "SELECT * FROM tasks WHERE user_id = ?"
        params: list[Any] = [user["id"]]

        priority = request.args.get("priority")
        if priority is not None:
            params.append(parse_priority(priority))
            sql += " AND priority = ?"

        due_date = request.args.get("due_date")
        if due_date is not None:
            params.append(parse_due_date(due_date))
            sql += " AND due_date = ?"

        due_before = request.args.get("due_before")
        if due_before is not None:
            params.append(parse_due_date(due_before))
            sql += " AND due_date <= ?"

        due_after = request.args.get("due_after")
        if due_after is not None:
            params.append(parse_due_date(due_after))
            sql += " AND due_date >= ?"

        sort_by = request.args.get("sort_by", "id")
        if sort_by not in {"id", "priority", "due_date"}:
            raise ValidationError("sort_by must be one of: id, priority, due_date")

        order = request.args.get("order", "asc").lower()
        if order not in {"asc", "desc"}:
            raise ValidationError("order must be 'asc' or 'desc'")

        sql += f" ORDER BY {sort_by} {order.upper()}, id ASC"
        rows = get_db().execute(sql, params).fetchall()
        return jsonify({"tasks": [task_to_dict(row) for row in rows]}), 200

    @app.get("/tasks/<int:task_id>")
    def get_task(task_id: int) -> Tuple[Any, int]:
        user, auth_error = authenticate()
        if auth_error:
            return auth_error
        assert user is not None

        task = fetch_task(task_id, user["id"])
        if task is None:
            return error_response("Task not found", 404)
        return jsonify({"task": task_to_dict(task)}), 200

    @app.put("/tasks/<int:task_id>")
    @app.patch("/tasks/<int:task_id>")
    def update_task(task_id: int) -> Tuple[Any, int]:
        user, auth_error = authenticate()
        if auth_error:
            return auth_error
        assert user is not None

        if fetch_task(task_id, user["id"]) is None:
            return error_response("Task not found", 404)

        payload = validate_task_payload(require_json_body(), partial=True)
        set_clause = ", ".join(f"{field} = ?" for field in payload)
        params = list(payload.values()) + [task_id, user["id"]]
        get_db().execute(
            f"UPDATE tasks SET {set_clause}, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND user_id = ?",
            params,
        )
        get_db().commit()
        task = fetch_task(task_id, user["id"])
        return jsonify({"task": task_to_dict(task)}), 200

    @app.delete("/tasks/<int:task_id>")
    def delete_task(task_id: int) -> Tuple[Any, int]:
        user, auth_error = authenticate()
        if auth_error:
            return auth_error
        assert user is not None

        task = fetch_task(task_id, user["id"])
        if task is None:
            return error_response("Task not found", 404)

        get_db().execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["id"]))
        get_db().commit()
        return jsonify({"message": "Task deleted", "id": task_id}), 200


def fetch_task(task_id: int, user_id: int) -> Optional[sqlite3.Row]:
    """Fetch one task by ID and user ID."""
    return (
        get_db()
        .execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        .fetchone()
    )


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
