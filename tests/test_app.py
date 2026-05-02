"""Tests for the Task Manager REST API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from flask.testing import FlaskClient

from src.app import create_app


@pytest.fixture()
def client(tmp_path: Path) -> FlaskClient:
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test_tasks.db"),
            "API_KEYS": {
                "alice-key": "alice",
                "bob-key": "bob",
            },
        }
    )
    return app.test_client()


def auth_headers(api_key: str = "alice-key") -> dict[str, str]:
    return {"X-API-Key": api_key}


def valid_task(**overrides: Any) -> dict[str, Any]:
    task = {
        "description": "Finish project documentation",
        "priority": "medium",
        "due_date": "2026-01-31",
    }
    task.update(overrides)
    return task


def create_task(client: FlaskClient, api_key: str = "alice-key", **overrides: Any) -> dict[str, Any]:
    response = client.post(
        "/tasks",
        json=valid_task(**overrides),
        headers=auth_headers(api_key),
    )
    assert response.status_code == 201
    data = response.get_json()
    assert isinstance(data, dict)
    return data


def test_create_task_with_valid_api_key_returns_201(client: FlaskClient) -> None:
    response = client.post(
        "/tasks",
        json=valid_task(priority="high"),
        headers=auth_headers(),
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] > 0
    assert data["description"] == "Finish project documentation"
    assert data["priority"] == "high"
    assert data["due_date"] == "2026-01-31"
    assert "created_at" in data
    assert "updated_at" in data


def test_missing_api_key_returns_401(client: FlaskClient) -> None:
    response = client.get("/tasks")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Missing API key"}


def test_invalid_api_key_returns_401(client: FlaskClient) -> None:
    response = client.get("/tasks", headers=auth_headers("bad-key"))

    assert response.status_code == 401
    assert response.get_json() == {"error": "Invalid API key"}


def test_invalid_due_date_returns_400(client: FlaskClient) -> None:
    response = client.post(
        "/tasks",
        json=valid_task(due_date="not-a-date"),
        headers=auth_headers(),
    )

    assert response.status_code == 400
    assert "due_date" in response.get_json()["error"]


def test_invalid_priority_returns_400(client: FlaskClient) -> None:
    response = client.post(
        "/tasks",
        json=valid_task(priority="urgent"),
        headers=auth_headers(),
    )

    assert response.status_code == 400
    assert "priority" in response.get_json()["error"]


def test_get_task_by_id_returns_task_for_owner(client: FlaskClient) -> None:
    task = create_task(client)

    response = client.get(f"/tasks/{task['id']}", headers=auth_headers())

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == task["id"]
    assert data["description"] == task["description"]


def test_delete_task_returns_204_and_removes_task(client: FlaskClient) -> None:
    task = create_task(client)

    delete_response = client.delete(f"/tasks/{task['id']}", headers=auth_headers())
    get_response = client.get(f"/tasks/{task['id']}", headers=auth_headers())

    assert delete_response.status_code == 204
    assert delete_response.data == b""
    assert get_response.status_code == 404


def test_put_task_updates_all_fields(client: FlaskClient) -> None:
    task = create_task(client)

    response = client.put(
        f"/tasks/{task['id']}",
        json=valid_task(
            description="Updated description",
            priority="low",
            due_date="2026-02-01T12:30:00+00:00",
        ),
        headers=auth_headers(),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["description"] == "Updated description"
    assert data["priority"] == "low"
    assert data["due_date"] == "2026-02-01T12:30:00+00:00"


def test_patch_task_updates_selected_fields(client: FlaskClient) -> None:
    task = create_task(client, priority="medium")

    response = client.patch(
        f"/tasks/{task['id']}",
        json={"priority": "HIGH"},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["description"] == task["description"]
    assert data["priority"] == "high"
    assert data["due_date"] == task["due_date"]


def test_list_tasks_only_returns_authenticated_users_tasks(client: FlaskClient) -> None:
    alice_task = create_task(client, "alice-key", description="Alice task")
    create_task(client, "bob-key", description="Bob task")

    response = client.get("/tasks", headers=auth_headers("alice-key"))

    assert response.status_code == 200
    data = response.get_json()
    assert [task["id"] for task in data["tasks"]] == [alice_task["id"]]
    assert data["tasks"][0]["description"] == "Alice task"


def test_user_cannot_access_another_users_task(client: FlaskClient) -> None:
    alice_task = create_task(client, "alice-key")

    response = client.get(f"/tasks/{alice_task['id']}", headers=auth_headers("bob-key"))

    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}


def test_authorization_bearer_header_is_supported(client: FlaskClient) -> None:
    response = client.get("/tasks", headers={"Authorization": "Bearer alice-key"})

    assert response.status_code == 200
    assert response.get_json() == {"tasks": []}
