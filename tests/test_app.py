"""Tests for the task manager REST API."""

from __future__ import annotations

import pytest

from src.app import create_app

API_KEY = "test-api-key"


@pytest.fixture()
def client():
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": ":memory:",
            "DEFAULT_API_KEY": API_KEY,
        }
    )
    return app.test_client()


def auth_headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


def create_task(client, **overrides):
    payload = {
        "title": "Write tests",
        "description": "Cover API endpoints",
        "priority": 3,
        "due_date": "2025-01-15",
    }
    payload.update(overrides)
    return client.post("/tasks", json=payload, headers=auth_headers())


def test_create_task_with_valid_api_key_returns_created_task(client):
    response = create_task(client)

    assert response.status_code == 201
    body = response.get_json()
    assert body["task"]["id"] == 1
    assert body["task"]["title"] == "Write tests"
    assert body["task"]["description"] == "Cover API endpoints"
    assert body["task"]["priority"] == 3
    assert body["task"]["due_date"] == "2025-01-15"


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "bad-key"}])
def test_missing_or_invalid_api_key_returns_unauthorized(client, headers):
    response = client.get("/tasks", headers=headers)

    assert response.status_code == 401
    assert "error" in response.get_json()


def test_update_task_with_invalid_date_returns_validation_error(client):
    task_id = create_task(client).get_json()["task"]["id"]

    response = client.patch(
        f"/tasks/{task_id}", json={"due_date": "01/15/2025"}, headers=auth_headers()
    )

    assert response.status_code == 400
    assert "due_date" in response.get_json()["error"]


def test_delete_existing_task_returns_success(client):
    task_id = create_task(client).get_json()["task"]["id"]

    response = client.delete(f"/tasks/{task_id}", headers=auth_headers())

    assert response.status_code == 200
    assert response.get_json() == {"message": "Task deleted", "id": task_id}
    missing = client.get(f"/tasks/{task_id}", headers=auth_headers())
    assert missing.status_code == 404


def test_list_tasks_with_priority_and_due_date_filters(client):
    create_task(client, title="Low", priority=1, due_date="2025-02-01")
    create_task(client, title="High early", priority=5, due_date="2025-01-01")
    create_task(client, title="High late", priority=5, due_date="2025-03-01")

    response = client.get(
        "/tasks?priority=5&due_before=2025-02-01&sort_by=due_date&order=desc",
        headers=auth_headers(),
    )

    assert response.status_code == 200
    tasks = response.get_json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "High early"


def test_read_specific_task_returns_details_or_not_found(client):
    task_id = create_task(client, title="Read me").get_json()["task"]["id"]

    found = client.get(f"/tasks/{task_id}", headers=auth_headers())
    missing = client.get("/tasks/999", headers=auth_headers())

    assert found.status_code == 200
    assert found.get_json()["task"]["title"] == "Read me"
    assert missing.status_code == 404
    assert missing.get_json()["error"] == "Task not found"
