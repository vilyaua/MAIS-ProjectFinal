from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import DEFAULT_API_KEY, create_app  # noqa: E402


@pytest.fixture()
def client(tmp_path: Path) -> Any:
    database_path = tmp_path / "test_tasks.db"
    app = create_app(str(database_path), seed_default_user=True)
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": DEFAULT_API_KEY}


def valid_task_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "title": "Write tests",
        "description": "Cover task manager endpoints",
        "priority": "high",
        "due_date": "2030-12-31",
    }
    payload.update(overrides)
    return payload


def create_task(client: Any, headers: dict[str, str], **overrides: Any) -> dict[str, Any]:
    response = client.post("/tasks", json=valid_task_payload(**overrides), headers=headers)
    assert response.status_code == 201
    return response.get_json()["task"]


def test_create_task_with_valid_api_key_saves_and_returns_success(
    client: Any, auth_headers: dict[str, str]
) -> None:
    response = client.post("/tasks", json=valid_task_payload(), headers=auth_headers)

    assert response.status_code == 201
    body = response.get_json()
    assert body["message"] == "Task created successfully."
    assert body["task"]["id"] == 1
    assert body["task"]["title"] == "Write tests"
    assert body["task"]["priority"] == "high"


def test_invalid_api_key_returns_unauthorized(client: Any) -> None:
    response = client.get("/tasks", headers={"X-API-Key": "invalid"})

    assert response.status_code == 401
    assert response.get_json() == {"error": "unauthorized", "message": "Invalid API key."}


def test_missing_api_key_returns_unauthorized(client: Any) -> None:
    response = client.get("/tasks")

    assert response.status_code == 401
    assert response.get_json() == {"error": "unauthorized", "message": "Missing API key."}


def test_fetching_tasks_returns_only_authenticated_users_tasks(
    client: Any, auth_headers: dict[str, str]
) -> None:
    first = create_task(client, auth_headers, title="First", due_date="2030-01-01")
    second = create_task(client, auth_headers, title="Second", priority="low", due_date="2030-02-01")

    response = client.get("/tasks", headers=auth_headers)

    assert response.status_code == 200
    tasks = response.get_json()["tasks"]
    assert [task["id"] for task in tasks] == [first["id"], second["id"]]
    assert tasks[0]["title"] == "First"
    assert tasks[1]["priority"] == "low"


def test_update_task_with_valid_changes_returns_updated_task(
    client: Any, auth_headers: dict[str, str]
) -> None:
    task = create_task(client, auth_headers)

    response = client.patch(
        f"/tasks/{task['id']}",
        json={"title": "Updated title", "priority": "medium"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["message"] == "Task updated successfully."
    assert body["task"]["title"] == "Updated title"
    assert body["task"]["priority"] == "medium"
    assert body["task"]["description"] == task["description"]


def test_delete_task_by_id_removes_task(client: Any, auth_headers: dict[str, str]) -> None:
    task = create_task(client, auth_headers)

    delete_response = client.delete(f"/tasks/{task['id']}", headers=auth_headers)
    fetch_response = client.get(f"/tasks/{task['id']}", headers=auth_headers)

    assert delete_response.status_code == 200
    assert delete_response.get_json() == {"message": "Task deleted successfully."}
    assert fetch_response.status_code == 404


@pytest.mark.parametrize(
    ("payload", "expected_field"),
    [
        ({"description": "Missing title", "priority": "low", "due_date": "2030-01-01"}, "title"),
        (valid_task_payload(priority="urgent"), "priority"),
        (valid_task_payload(due_date="01-01-2030"), "due_date"),
        (valid_task_payload(title=""), "title"),
        (valid_task_payload(description=10), "description"),
    ],
)
def test_create_task_invalid_input_returns_validation_error(
    client: Any,
    auth_headers: dict[str, str],
    payload: dict[str, Any],
    expected_field: str,
) -> None:
    response = client.post("/tasks", json=payload, headers=auth_headers)

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "validation_error"
    assert expected_field in body["messages"]


def test_update_task_invalid_input_returns_validation_error(
    client: Any, auth_headers: dict[str, str]
) -> None:
    task = create_task(client, auth_headers)

    response = client.put(
        f"/tasks/{task['id']}",
        json={"priority": "critical", "due_date": "not-a-date"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    messages = response.get_json()["messages"]
    assert "priority" in messages
    assert "due_date" in messages


def test_bearer_authorization_header_is_supported(client: Any) -> None:
    response = client.get("/tasks", headers={"Authorization": f"Bearer {DEFAULT_API_KEY}"})

    assert response.status_code == 200
    assert response.get_json() == {"tasks": []}
