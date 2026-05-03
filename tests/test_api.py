from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from task_manager import create_app


@pytest.fixture()
def app(tmp_path: Path):
    database_path = tmp_path / "test.sqlite3"
    app = create_app(str(database_path), testing=True)
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def create_user(client, username: str = "alice", api_key: str = "valid-key") -> dict[str, Any]:
    response = client.post("/users", json={"username": username, "api_key": api_key})
    assert response.status_code == 201
    return response.get_json()


def auth_headers(api_key: str = "valid-key") -> dict[str, str]:
    return {"X-API-Key": api_key}


def valid_task_payload() -> dict[str, Any]:
    return {
        "title": "Write tests",
        "description": "Cover the task API",
        "priority": 3,
        "due_date": "2026-01-31",
    }


def test_create_task_with_valid_api_key_persists_task(client):
    create_user(client)

    response = client.post("/tasks", json=valid_task_payload(), headers=auth_headers())

    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 1
    assert data["title"] == "Write tests"
    assert data["description"] == "Cover the task API"
    assert data["priority"] == 3
    assert data["due_date"] == "2026-01-31"

    list_response = client.get("/tasks", headers=auth_headers())
    assert list_response.status_code == 200
    assert list_response.get_json()["tasks"] == [data]


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "bad-key"}])
def test_missing_or_invalid_api_key_returns_unauthorized(client, headers):
    create_user(client)

    response = client.get("/tasks", headers=headers)

    assert response.status_code == 401
    assert "error" in response.get_json()


def test_get_tasks_returns_only_authenticated_users_tasks(client):
    create_user(client, "alice", "alice-key")
    create_user(client, "bob", "bob-key")
    client.post("/tasks", json={**valid_task_payload(), "title": "Alice"}, headers=auth_headers("alice-key"))
    client.post("/tasks", json={**valid_task_payload(), "title": "Bob"}, headers=auth_headers("bob-key"))

    response = client.get("/tasks", headers=auth_headers("alice-key"))

    assert response.status_code == 200
    tasks = response.get_json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Alice"


def test_update_task_with_valid_api_key(client):
    create_user(client)
    create_response = client.post("/tasks", json=valid_task_payload(), headers=auth_headers())
    task_id = create_response.get_json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated", "priority": 5},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Updated"
    assert data["priority"] == 5
    assert data["description"] == "Cover the task API"


def test_delete_task_with_valid_api_key(client):
    create_user(client)
    create_response = client.post("/tasks", json=valid_task_payload(), headers=auth_headers())
    task_id = create_response.get_json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers=auth_headers())

    assert response.status_code == 204
    list_response = client.get("/tasks", headers=auth_headers())
    assert list_response.get_json()["tasks"] == []


@pytest.mark.parametrize(
    "payload, expected_message",
    [
        ({"description": "Missing fields", "priority": 1, "due_date": "2026-01-31"}, "Missing"),
        ({**valid_task_payload(), "priority": 6}, "priority"),
        ({**valid_task_payload(), "priority": 0}, "priority"),
        ({**valid_task_payload(), "priority": "high"}, "priority"),
        ({**valid_task_payload(), "due_date": "01-31-2026"}, "due_date"),
        ({**valid_task_payload(), "due_date": "2026-02-30"}, "due_date"),
    ],
)
def test_invalid_create_payload_returns_bad_request(client, payload, expected_message):
    create_user(client)

    response = client.post("/tasks", json=payload, headers=auth_headers())

    assert response.status_code == 400
    assert expected_message in response.get_json()["error"]


def test_invalid_update_payload_returns_bad_request(client):
    create_user(client)
    create_response = client.post("/tasks", json=valid_task_payload(), headers=auth_headers())
    task_id = create_response.get_json()["id"]

    response = client.put(f"/tasks/{task_id}", json={"due_date": "not-a-date"}, headers=auth_headers())

    assert response.status_code == 400
    assert "due_date" in response.get_json()["error"]


def test_database_errors_return_500(client, app, monkeypatch):
    create_user(client)

    def broken_get_db():
        raise sqlite3.DatabaseError("boom")

    monkeypatch.setattr("task_manager.app.get_db", broken_get_db)

    response = client.get("/tasks", headers=auth_headers())

    assert response.status_code == 500
    assert "Database error" in response.get_json()["error"]
