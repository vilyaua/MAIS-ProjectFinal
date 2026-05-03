"""Tests for the Task Manager REST API."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from flask.testing import FlaskClient
from src.app import create_app

API_KEY = "test-api-key"


@pytest.fixture()
def client(tmp_path: Path) -> Generator[FlaskClient, None, None]:
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "tasks.sqlite3"),
            "API_KEYS": {API_KEY},
        }
    )
    with app.test_client() as test_client:
        yield test_client


def auth_headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


def valid_task_payload() -> dict[str, str]:
    return {
        "title": "Finish report",
        "description": "Prepare the weekly status report",
        "priority": "high",
        "due_date": "2026-01-15",
    }


def create_task(client: FlaskClient) -> dict[str, object]:
    response = client.post("/tasks", json=valid_task_payload(), headers=auth_headers())
    assert response.status_code == 201
    return response.get_json()


def test_create_task_with_valid_api_key_returns_201(client: FlaskClient) -> None:
    response = client.post("/tasks", json=valid_task_payload(), headers=auth_headers())

    assert response.status_code == 201
    body = response.get_json()
    assert body["id"] == 1
    assert body["title"] == "Finish report"
    assert body["description"] == "Prepare the weekly status report"
    assert body["priority"] == "high"
    assert body["due_date"] == "2026-01-15"
    assert "created_at" in body
    assert "updated_at" in body


def test_missing_or_invalid_api_key_returns_401(client: FlaskClient) -> None:
    missing_response = client.get("/tasks")
    invalid_response = client.get("/tasks", headers={"X-API-Key": "wrong"})

    assert missing_response.status_code == 401
    assert invalid_response.status_code == 401
    assert missing_response.get_json()["error"] == "Unauthorized"
    assert invalid_response.get_json()["error"] == "Unauthorized"


def test_retrieve_task_by_id_with_valid_api_key(client: FlaskClient) -> None:
    task = create_task(client)

    response = client.get(f"/tasks/{task['id']}", headers=auth_headers())

    assert response.status_code == 200
    body = response.get_json()
    assert body["id"] == task["id"]
    assert body["title"] == task["title"]


def test_update_task_with_valid_data(client: FlaskClient) -> None:
    task = create_task(client)
    update_payload = {
        "title": "Updated report",
        "priority": "medium",
        "due_date": "2026-02-01",
    }

    response = client.put(f"/tasks/{task['id']}", json=update_payload, headers=auth_headers())

    assert response.status_code == 200
    body = response.get_json()
    assert body["id"] == task["id"]
    assert body["title"] == "Updated report"
    assert body["description"] == task["description"]
    assert body["priority"] == "medium"
    assert body["due_date"] == "2026-02-01"


def test_delete_task_removes_task(client: FlaskClient) -> None:
    task = create_task(client)

    delete_response = client.delete(f"/tasks/{task['id']}", headers=auth_headers())
    get_response = client.get(f"/tasks/{task['id']}", headers=auth_headers())

    assert delete_response.status_code == 204
    assert delete_response.data == b""
    assert get_response.status_code == 404


@pytest.mark.parametrize(
    "payload, expected_field",
    [
        ({"description": "Missing title", "priority": "low", "due_date": "2026-01-15"}, "title"),
        (
            {
                "title": "Bad date",
                "description": "Invalid",
                "priority": "low",
                "due_date": "15-01-2026",
            },
            "due_date",
        ),
        (
            {
                "title": "Bad priority",
                "description": "Invalid",
                "priority": "urgent",
                "due_date": "2026-01-15",
            },
            "priority",
        ),
    ],
)
def test_invalid_create_input_returns_400(
    client: FlaskClient, payload: dict[str, str], expected_field: str
) -> None:
    response = client.post("/tasks", json=payload, headers=auth_headers())

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "Bad Request"
    assert expected_field in body["details"]


def test_invalid_update_input_returns_400(client: FlaskClient) -> None:
    task = create_task(client)

    response = client.put(
        f"/tasks/{task['id']}",
        json={"due_date": "2026-13-99"},
        headers=auth_headers(),
    )

    assert response.status_code == 400
    assert "due_date" in response.get_json()["details"]


def test_list_all_tasks_with_valid_api_key(client: FlaskClient) -> None:
    first = create_task(client)
    second_payload = valid_task_payload() | {
        "title": "Buy supplies",
        "priority": "low",
        "due_date": "2026-03-20",
    }
    second_response = client.post("/tasks", json=second_payload, headers=auth_headers())
    assert second_response.status_code == 201

    response = client.get("/tasks", headers=auth_headers())

    assert response.status_code == 200
    body = response.get_json()
    assert len(body["tasks"]) == 2
    assert body["tasks"][0]["id"] == first["id"]
    assert body["tasks"][1]["title"] == "Buy supplies"


def test_query_parameter_api_key_is_accepted(client: FlaskClient) -> None:
    response = client.get(f"/tasks?api_key={API_KEY}")

    assert response.status_code == 200
    assert response.get_json() == {"tasks": []}
