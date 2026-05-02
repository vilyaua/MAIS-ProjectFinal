"""Tests for the task manager Flask API."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from flask.testing import FlaskClient

from src.app import create_app

API_KEY = "valid-test-key"
HEADERS = {"X-API-Key": API_KEY}


@pytest.fixture()
def client(tmp_path: Path) -> FlaskClient:
    """Create a test client backed by an isolated SQLite database."""
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "tasks.sqlite"),
            "API_KEYS": {API_KEY},
        }
    )
    return app.test_client()


def future_date(days: int = 7) -> str:
    """Return an ISO-formatted date in the future."""
    return (date.today() + timedelta(days=days)).isoformat()


def make_task(**overrides: Any) -> dict[str, Any]:
    """Build a valid task payload with optional overrides."""
    payload: dict[str, Any] = {
        "description": "Write API tests",
        "priority": 3,
        "due_date": future_date(),
        "status": "pending",
    }
    payload.update(overrides)
    return payload


def create_task(client: FlaskClient, **overrides: Any) -> dict[str, Any]:
    """Create a task and return its JSON representation."""
    response = client.post("/tasks", json=make_task(**overrides), headers=HEADERS)
    assert response.status_code == 201
    return response.get_json()


def test_create_task_with_valid_api_key_saves_and_returns_task(client: FlaskClient) -> None:
    payload = make_task(description="Finish documentation", priority=2)

    response = client.post("/tasks", json=payload, headers=HEADERS)

    assert response.status_code == 201
    body = response.get_json()
    assert body["id"] == 1
    assert body["description"] == "Finish documentation"
    assert body["priority"] == 2
    assert body["due_date"] == payload["due_date"]
    assert body["status"] == "pending"
    assert "created_at" in body
    assert "updated_at" in body

    list_response = client.get("/tasks", headers=HEADERS)
    assert list_response.status_code == 200
    assert list_response.get_json()["tasks"] == [body]


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong-key"}])
def test_missing_or_invalid_api_key_returns_unauthorized(
    client: FlaskClient, headers: dict[str, str]
) -> None:
    response = client.get("/tasks", headers=headers)

    assert response.status_code == 401
    body = response.get_json()
    assert body["error"] == "Unauthorized"
    assert "API key" in body["message"]


def test_get_tasks_with_priority_filter_returns_matching_tasks(client: FlaskClient) -> None:
    first = create_task(client, description="High priority", priority=5)
    create_task(client, description="Low priority", priority=1)
    second = create_task(client, description="Another high priority", priority=5)

    response = client.get("/tasks?priority=5", headers=HEADERS)

    assert response.status_code == 200
    assert response.get_json()["tasks"] == [first, second]


def test_put_with_invalid_due_date_format_returns_bad_request(client: FlaskClient) -> None:
    task = create_task(client)

    response = client.put(
        f"/tasks/{task['id']}", json={"due_date": "12/31/2099"}, headers=HEADERS
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "Bad Request"
    assert "YYYY-MM-DD" in body["message"]


def test_delete_nonexistent_task_returns_not_found(client: FlaskClient) -> None:
    response = client.delete("/tasks/999", headers=HEADERS)

    assert response.status_code == 404
    assert response.get_json()["error"] == "Not Found"


def test_get_tasks_without_filters_returns_all_tasks(client: FlaskClient) -> None:
    first = create_task(client, description="Task one", priority=1)
    second = create_task(client, description="Task two", priority=4)

    response = client.get("/tasks", headers=HEADERS)

    assert response.status_code == 200
    assert response.get_json()["tasks"] == [first, second]


def test_create_task_missing_required_fields_returns_bad_request(client: FlaskClient) -> None:
    response = client.post(
        "/tasks",
        json={"description": "Incomplete task", "priority": 2},
        headers=HEADERS,
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "Bad Request"
    assert "Missing required field" in body["message"]
    assert "due_date" in body["message"]
    assert "status" in body["message"]


@pytest.mark.parametrize(
    ("payload", "expected_message"),
    [
        ({"description": "   "}, "description must be a non-empty string"),
        ({"priority": 0}, "priority must be between 1 and 5"),
        ({"priority": 6}, "priority must be between 1 and 5"),
        ({"due_date": date.today().isoformat()}, "due_date must be a future date"),
        ({"status": "unknown"}, "status must be one of"),
    ],
)
def test_update_validation_edge_cases(
    client: FlaskClient, payload: dict[str, Any], expected_message: str
) -> None:
    task = create_task(client)

    response = client.put(f"/tasks/{task['id']}", json=payload, headers=HEADERS)

    assert response.status_code == 400
    assert expected_message in response.get_json()["message"]


def test_due_date_filter_returns_matching_tasks(client: FlaskClient) -> None:
    soon = future_date(3)
    later = future_date(10)
    expected = create_task(client, description="Soon", due_date=soon)
    create_task(client, description="Later", due_date=later)

    response = client.get(f"/tasks?due_date={soon}", headers=HEADERS)

    assert response.status_code == 200
    assert response.get_json()["tasks"] == [expected]


def test_get_update_and_delete_task_lifecycle(client: FlaskClient) -> None:
    task = create_task(client, status="pending")

    get_response = client.get(f"/tasks/{task['id']}", headers=HEADERS)
    assert get_response.status_code == 200
    assert get_response.get_json() == task

    update_response = client.put(
        f"/tasks/{task['id']}", json={"status": "completed"}, headers=HEADERS
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["status"] == "completed"

    delete_response = client.delete(f"/tasks/{task['id']}", headers=HEADERS)
    assert delete_response.status_code == 200
    assert delete_response.get_json()["message"] == "Task deleted."

    missing_response = client.get(f"/tasks/{task['id']}", headers=HEADERS)
    assert missing_response.status_code == 404
