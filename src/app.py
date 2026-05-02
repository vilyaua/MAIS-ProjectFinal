"""Flask Task Manager REST API backed by SQLite.

The application exposes CRUD endpoints for tasks. Each request must be
associated with a user through a valid API key, and task access is scoped to
that authenticated user.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from flask import Flask, Response, g, jsonify, request

ALLOWED_PRIORITIES = {"low", "medium", "high"}
DEFAULT_API_KEYS = {
    "dev-api-key-1": "alice",
    "dev-api-key-2": "bob",
}


class ValidationError(ValueError):
    """Raised when request payload validation fails."""


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        test_config: Optional configuration overrides. Useful keys are
            ``DATABASE`` and ``API_KEYS``.

    Returns:
        Configured Flask app instance.
    """

    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=str(Path(__file__).resolve().parent.parent / "tasks.db"),
        API_KEYS=DEFAULT_API_KEYS,
    )

    if test_config:
        app.config.update(test_config)

    @app.before_request
    def authenticate_request() -> tuple[Response, int] | None:
        if request.endpoint in {"health"}:
            return None

        api_key = _extract_api_key()
        if not api_key:
            return _error_response("Missing API key", 401)

        user = get_user_by_api_key(api_key)
        if user is None:
            return _error_response("Invalid API key", 401)

        g.current_user = user
        return None

    @app.teardown_appcontext
    def close_db(error: BaseException | None = None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
        return _error_response(str(error), 400)

    @app.errorhandler(404)
    def handle_not_found(error: Exception) -> tuple[Response, int]:
        return _error_response("Resource not found", 404)

    @app.errorhandler(405)
    def handle_method_not_allowed(error: Exception) -> tuple[Response, int]:
        return _error_response("Method not allowed", 405)

    @app.errorhandler(500)
    def handle_internal_error(error: Exception) -> tuple[Response, int]:
        return _error_response("Internal server error", 500)

    @app.route("/health", methods=["GET"])
    def health() -> tuple[Response, int]:
        return jsonify({"status": "ok"}), 200

    @app.route("/tasks", methods=["POST"])
    def create_task() -> tuple[Response, int]:
        payload = _get_json_payload()
        task_data = _validate_task_payload(payload, require_all=True)
        now = _utc_now_iso()

        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO tasks (
                user_id, description, priority, due_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                g.current_user["id"],
                task_data["description"],
                task_data["priority"],
                task_data["due_date"],
                now,
                now,
            ),
        )
        db.commit()

        task = get_task_for_current_user(cursor.lastrowid)
        return jsonify(_task_to_dict(task)), 201

    @app.route("/tasks", methods=["GET"])
    def list_tasks() -> tuple[Response, int]:
        rows = get_db().execute(
            """
            SELECT id, user_id, description, priority, due_date, created_at, updated_at
            FROM tasks
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (g.current_user["id"],),
        ).fetchall()
        return jsonify({"tasks": [_task_to_dict(row) for row in rows]}), 200

    @app.route("/tasks/<int:task_id>", methods=["GET"])
    def get_task(task_id: int) -> tuple[Response, int]:
        task = get_task_for_current_user(task_id)
        if task is None:
            return _error_response("Task not found", 404)
        return jsonify(_task_to_dict(task)), 200

    @app.route("/tasks/<int:task_id>", methods=["PUT"])
    def replace_task(task_id: int) -> tuple[Response, int]:
        existing = get_task_for_current_user(task_id)
        if existing is None:
            return _error_response("Task not found", 404)

        payload = _get_json_payload()
        task_data = _validate_task_payload(payload, require_all=True)
        updated = _update_task(task_id, task_data)
        return jsonify(_task_to_dict(updated)), 200

    @app.route("/tasks/<int:task_id>", methods=["PATCH"])
    def update_task(task_id: int) -> tuple[Response, int]:
        existing = get_task_for_current_user(task_id)
        if existing is None:
            return _error_response("Task not found", 404)

        payload = _get_json_payload()
        task_data = _validate_task_payload(payload, require_all=False)
        merged = {
            "description": task_data.get("description", existing["description"]),
            "priority": task_data.get("priority", existing["priority"]),
            "due_date": task_data.get("due_date", existing["due_date"]),
        }
        updated = _update_task(task_id, merged)
        return jsonify(_task_to_dict(updated)), 200

    @app.route("/tasks/<int:task_id>", methods=["DELETE"])
    def delete_task(task_id: int) -> tuple[str, int]:
        existing = get_task_for_current_user(task_id)
        if existing is None:
            return "", 404

        db = get_db()
        db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, g.current_user["id"]),
        )
        db.commit()
        return "", 204

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    def init_db() -> None:
        db = get_db()
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                api_key TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
                due_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """
        )

        for api_key, username in app.config["API_KEYS"].items():
            db.execute(
                """
                INSERT INTO users (username, api_key)
                VALUES (?, ?)
                ON CONFLICT(api_key) DO UPDATE SET username = excluded.username
                """,
                (username, api_key),
            )
        db.commit()

    def get_user_by_api_key(api_key: str) -> sqlite3.Row | None:
        return get_db().execute(
            "SELECT id, username, api_key FROM users WHERE api_key = ?",
            (api_key,),
        ).fetchone()

    def get_task_for_current_user(task_id: int) -> sqlite3.Row | None:
        return get_db().execute(
            """
            SELECT id, user_id, description, priority, due_date, created_at, updated_at
            FROM tasks
            WHERE id = ? AND user_id = ?
            """,
            (task_id, g.current_user["id"]),
        ).fetchone()

    def _update_task(task_id: int, task_data: dict[str, str]) -> sqlite3.Row:
        now = _utc_now_iso()
        db = get_db()
        db.execute(
            """
            UPDATE tasks
            SET description = ?, priority = ?, due_date = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                task_data["description"],
                task_data["priority"],
                task_data["due_date"],
                now,
                task_id,
                g.current_user["id"],
            ),
        )
        db.commit()
        task = get_task_for_current_user(task_id)
        if task is None:
            raise RuntimeError("Updated task could not be loaded")
        return task

    app.get_db = get_db  # type: ignore[attr-defined]
    app.init_db = init_db  # type: ignore[attr-defined]

    with app.app_context():
        init_db()

    return app


def _extract_api_key() -> str | None:
    """Read API key from X-API-Key or Authorization: Bearer header."""

    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key.strip()

    authorization = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if authorization.startswith(prefix):
        return authorization[len(prefix) :].strip()
    return None


def _get_json_payload() -> dict[str, Any]:
    if not request.is_json:
        raise ValidationError("Request body must be JSON")

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("JSON body must be an object")
    return payload


def _validate_task_payload(
    payload: dict[str, Any], *, require_all: bool
) -> dict[str, str]:
    allowed_fields = {"description", "priority", "due_date"}
    unknown_fields = sorted(set(payload) - allowed_fields)
    if unknown_fields:
        fields = ", ".join(unknown_fields)
        raise ValidationError(f"Unknown task field(s): {fields}")

    if require_all:
        missing = sorted(field for field in allowed_fields if field not in payload)
        if missing:
            fields = ", ".join(missing)
            raise ValidationError(f"Missing required field(s): {fields}")
    elif not payload:
        raise ValidationError("At least one task field is required")

    validated: dict[str, str] = {}

    if "description" in payload:
        description = payload["description"]
        if not isinstance(description, str) or not description.strip():
            raise ValidationError("description must be a non-empty string")
        validated["description"] = description.strip()

    if "priority" in payload:
        priority = payload["priority"]
        if not isinstance(priority, str):
            raise ValidationError("priority must be a string")
        normalized_priority = priority.lower().strip()
        if normalized_priority not in ALLOWED_PRIORITIES:
            allowed = ", ".join(sorted(ALLOWED_PRIORITIES))
            raise ValidationError(f"priority must be one of: {allowed}")
        validated["priority"] = normalized_priority

    if "due_date" in payload:
        due_date = payload["due_date"]
        if not isinstance(due_date, str) or not due_date.strip():
            raise ValidationError("due_date must be a non-empty ISO 8601 date string")
        _validate_iso8601_date(due_date.strip())
        validated["due_date"] = due_date.strip()

    return validated


def _validate_iso8601_date(value: str) -> None:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError("due_date must be a valid ISO 8601 date string") from exc


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _task_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "description": row["description"],
        "priority": row["priority"],
        "due_date": row["due_date"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _error_response(message: str, status_code: int) -> tuple[Response, int]:
    return jsonify({"error": message}), status_code


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
