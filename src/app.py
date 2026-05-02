"""Flask application for a task manager REST API backed by SQLite."""

from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
import threading
from datetime import date, datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, ParamSpec, TypeVar, cast

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

DEFAULT_DATABASE = Path(__file__).resolve().parent.parent / "tasks.db"
DEFAULT_API_KEY = "change-me-development-key"
VALID_PRIORITIES = range(1, 6)

P = ParamSpec("P")
R = TypeVar("R")


class ValidationError(ValueError):
    """Raised when request payload validation fails."""


class Database:
    """Small SQLite helper with a process-local lock for safe writes."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self.lock = threading.RLock()

    def connect(self) -> sqlite3.Connection:
        """Create a SQLite connection suitable for Flask request contexts."""
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
            isolation_level=None,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def initialize(self) -> None:
        """Create application tables when they do not already exist."""
        with self.lock:
            connection = self.connect()
            try:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        description TEXT NOT NULL,
                        priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 5),
                        due_date TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            finally:
                connection.close()


def create_app(config: dict[str, Any] | None = None) -> Flask:
    """Application factory.

    Configuration keys:
    - DATABASE: SQLite database path. Defaults to ./tasks.db.
    - API_KEY_HASHES: iterable of SHA-256 hex digests for accepted API keys.
    - API_KEYS: iterable of plaintext keys; hashed at startup for convenience.
    - API_KEY: single plaintext API key fallback.
    """
    app = Flask(__name__)
    app.config.update(
        DATABASE=str(DEFAULT_DATABASE),
        API_KEY=os.environ.get("TASK_API_KEY", DEFAULT_API_KEY),
        API_KEY_HASHES=[],
    )
    if config:
        app.config.update(config)

    api_key_hashes = _load_api_key_hashes(app.config)
    if not api_key_hashes:
        raise RuntimeError("At least one API key or API key hash must be configured")
    app.config["API_KEY_HASHES"] = api_key_hashes

    database = Database(app.config["DATABASE"])
    database.initialize()
    app.extensions["task_database"] = database

    @app.teardown_appcontext
    def close_connection(_exception: BaseException | None) -> None:
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> tuple[Any, int]:
        return jsonify({"error": "validation_error", "message": str(error)}), 400

    @app.errorhandler(sqlite3.DatabaseError)
    def handle_database_error(error: sqlite3.DatabaseError) -> tuple[Any, int]:
        app.logger.exception("Database error: %s", error)
        return (
            jsonify(
                {
                    "error": "database_error",
                    "message": "A database error occurred while processing the request.",
                }
            ),
            500,
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException) -> tuple[Any, int]:
        return (
            jsonify(
                {
                    "error": error.name.lower().replace(" ", "_"),
                    "message": error.description,
                }
            ),
            error.code or 500,
        )

    @app.post("/tasks")
    @require_api_key
    def create_task() -> tuple[Any, int]:
        payload = _json_payload()
        task_data = _validate_task_payload(payload, partial=False)
        db = get_db()
        database = _database()
        with database.lock:
            cursor = db.execute(
                """
                INSERT INTO tasks (description, priority, due_date, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    task_data["description"],
                    task_data["priority"],
                    task_data["due_date"],
                ),
            )
            task = _get_task_by_id(cursor.lastrowid)
        return jsonify({"task": task}), 201

    @app.get("/tasks")
    @require_api_key
    def list_tasks() -> tuple[Any, int]:
        priority_filter = request.args.get("priority")
        due_before = request.args.get("due_before")
        due_after = request.args.get("due_after")
        sort = request.args.get("sort", "id")
        order = request.args.get("order", "asc")

        filters: list[str] = []
        parameters: list[Any] = []

        if priority_filter is not None:
            try:
                priority = int(priority_filter)
            except (TypeError, ValueError) as exc:
                raise ValidationError("priority filter must be an integer") from exc
            _validate_priority(priority)
            filters.append("priority = ?")
            parameters.append(priority)

        if due_before is not None:
            before_date = _parse_date(due_before, field_name="due_before")
            filters.append("due_date <= ?")
            parameters.append(before_date.isoformat())

        if due_after is not None:
            after_date = _parse_date(due_after, field_name="due_after")
            filters.append("due_date >= ?")
            parameters.append(after_date.isoformat())

        sort_columns = {
            "id": "id",
            "priority": "priority",
            "due_date": "due_date",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        if sort not in sort_columns:
            raise ValidationError(
                "sort must be one of: id, priority, due_date, created_at, updated_at"
            )
        if order.lower() not in {"asc", "desc"}:
            raise ValidationError("order must be either 'asc' or 'desc'")

        query = "SELECT * FROM tasks"
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += f" ORDER BY {sort_columns[sort]} {order.upper()}"

        rows = get_db().execute(query, parameters).fetchall()
        return jsonify({"tasks": [_row_to_task(row) for row in rows]}), 200

    @app.get("/tasks/<int:task_id>")
    @require_api_key
    def get_task(task_id: int) -> tuple[Any, int]:
        task = _get_task_by_id(task_id)
        if task is None:
            return jsonify({"error": "not_found", "message": "Task not found"}), 404
        return jsonify({"task": task}), 200

    @app.put("/tasks/<int:task_id>")
    @require_api_key
    def update_task(task_id: int) -> tuple[Any, int]:
        payload = _json_payload()
        task_data = _validate_task_payload(payload, partial=True)
        if not task_data:
            raise ValidationError("At least one task field must be provided")

        assignments = [f"{column} = ?" for column in task_data]
        values = list(task_data.values())
        values.append(task_id)

        database = _database()
        with database.lock:
            cursor = get_db().execute(
                f"""
                UPDATE tasks
                SET {', '.join(assignments)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                values,
            )
            if cursor.rowcount == 0:
                return jsonify({"error": "not_found", "message": "Task not found"}), 404
            task = _get_task_by_id(task_id)
        return jsonify({"task": task}), 200

    @app.patch("/tasks/<int:task_id>")
    @require_api_key
    def patch_task(task_id: int) -> tuple[Any, int]:
        return update_task(task_id)

    @app.delete("/tasks/<int:task_id>")
    @require_api_key
    def delete_task(task_id: int) -> tuple[Any, int]:
        database = _database()
        with database.lock:
            cursor = get_db().execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            if cursor.rowcount == 0:
                return jsonify({"error": "not_found", "message": "Task not found"}), 404
        return jsonify({"message": "Task deleted", "id": task_id}), 200

    @app.get("/health")
    def health() -> tuple[Any, int]:
        return jsonify({"status": "ok"}), 200

    return app


def _database() -> Database:
    return cast(Database, current_app_extensions()["task_database"])


def current_app_extensions() -> dict[str, Any]:
    """Return Flask current_app.extensions without importing it globally for tests."""
    from flask import current_app

    return current_app.extensions


def get_db() -> sqlite3.Connection:
    """Return the SQLite connection for the current request context."""
    if "db" not in g:
        g.db = _database().connect()
    return cast(sqlite3.Connection, g.db)


def require_api_key(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that authenticates requests with X-API-Key or Bearer token."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | tuple[Any, int]:
        supplied_key = _extract_api_key()
        if not supplied_key or not _is_valid_api_key(supplied_key):
            return (
                jsonify(
                    {
                        "error": "unauthorized",
                        "message": "A valid API key is required.",
                    }
                ),
                401,
            )
        return func(*args, **kwargs)

    return wrapper


def _extract_api_key() -> str | None:
    header_key = request.headers.get("X-API-Key")
    if header_key:
        return header_key.strip()
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def _is_valid_api_key(supplied_key: str) -> bool:
    supplied_hash = _hash_api_key(supplied_key)
    for stored_hash in current_app_extensions()["task_api_key_hashes"]:
        if hmac.compare_digest(supplied_hash, stored_hash):
            return True
    return False


def _load_api_key_hashes(config: dict[str, Any]) -> list[str]:
    configured_hashes = list(config.get("API_KEY_HASHES") or [])
    plaintext_keys = list(config.get("API_KEYS") or [])
    single_key = config.get("API_KEY")
    if single_key:
        plaintext_keys.append(str(single_key))

    hashes = [str(key_hash).lower() for key_hash in configured_hashes]
    hashes.extend(_hash_api_key(str(key)) for key in plaintext_keys if str(key))

    # De-duplicate while preserving order.
    unique_hashes = list(dict.fromkeys(hashes))
    return unique_hashes


def _hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def _json_payload() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")
    return payload


def _validate_task_payload(payload: dict[str, Any], *, partial: bool) -> dict[str, Any]:
    allowed_fields = {"description", "priority", "due_date"}
    unknown_fields = set(payload) - allowed_fields
    if unknown_fields:
        raise ValidationError(
            "Unknown field(s): " + ", ".join(sorted(unknown_fields))
        )

    required_fields = allowed_fields if not partial else set()
    missing_fields = required_fields - set(payload)
    if missing_fields:
        raise ValidationError(
            "Missing required field(s): " + ", ".join(sorted(missing_fields))
        )

    validated: dict[str, Any] = {}
    if "description" in payload:
        description = payload["description"]
        if not isinstance(description, str) or not description.strip():
            raise ValidationError("description must be a non-empty string")
        validated["description"] = description.strip()

    if "priority" in payload:
        try:
            priority = int(payload["priority"])
        except (TypeError, ValueError) as exc:
            raise ValidationError("priority must be an integer between 1 and 5") from exc
        _validate_priority(priority)
        validated["priority"] = priority

    if "due_date" in payload:
        due_date = _parse_date(str(payload["due_date"]), field_name="due_date")
        if due_date <= date.today():
            raise ValidationError("due_date must be a future date")
        validated["due_date"] = due_date.isoformat()

    return validated


def _validate_priority(priority: int) -> None:
    if priority not in VALID_PRIORITIES:
        raise ValidationError("priority must be an integer between 1 and 5")


def _parse_date(value: str, *, field_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid date in YYYY-MM-DD format") from exc


def _get_task_by_id(task_id: int) -> dict[str, Any] | None:
    row = get_db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return None
    return _row_to_task(row)


def _row_to_task(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "description": row["description"],
        "priority": row["priority"],
        "due_date": row["due_date"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# Store hashes in current_app.extensions after app creation by wrapping factory setup.
_original_create_app = create_app


def create_app(config: dict[str, Any] | None = None) -> Flask:  # type: ignore[no-redef]
    app = _original_create_app(config)
    app.extensions["task_api_key_hashes"] = app.config["API_KEY_HASHES"]
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=False)
