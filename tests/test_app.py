"""Tests for the task manager REST API."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.app import create_app

API_KEY = "test-api-key"


@pytest.fixture(name="app")
def app_fixture(tmp_path: Path) -> Flask:
    database_path = tmp_path / "tasks_test.db"
    app = create_app({"TESTING": True, "DATABASE": str(database_path), "API_KEY": API_KEY})
    return app


@pytest.fixture(name="client")
def client_fixture(app: Flask) -> FlaskClient:
    return app.test_client()


def auth_headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


def future_date(days: int = 5) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def create_task(
    client: FlaskClient,
    description: str = "Write tests",
    priority: int = 3,
    due_date: str | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/tasks",
        json={
            "description": description,
            "priority": priority,
            "due_date": due_date or future_date(),
        },
        headers=auth_headers(),
    )
    assert response.status_code == 201
    return response.get_json()["task"]


def test_create_task_with_valid_api_key(client: FlaskClient) -> None:
    task = create_task(client, "Finish API", 4)

    assert task["id"] == 1
    assert task["description"] == "Finish API"
    assert task["priority"] == 4
    assert task["due_date"] == future_date()
    assert "created_at" in task
    assert "updated_at" in task


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}])
def test_secured_endpoints_reject_missing_or_invalid_api_key(
    client: FlaskClient, headers: dict[str, str]
) -> None:
    response = client.get("/tasks", headers=headers)

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


@pytest.mark.parametrize(
    "payload, expected_message",
    [
        (
            {"description": "Bad priority", "priority": -1, "due_date": future_date()},
            "priority",
        ),
        (
            {
                "description": "Past date",
                "priority": 2,
                "due_date": (date.today() - timedelta(days=1)).isoformat(),
            },
            "future date",
        ),
        ({"description": "Missing fields"}, "Missing required"),
        ({"description": "", "priority": 1, "due_date": future_date()}, "description"),
    ],
)
def test_create_task_validation_errors(
    client: FlaskClient, payload: dict[str, Any], expected_message: str
) -> None:
    response = client.post("/tasks", json=payload, headers=auth_headers())

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "validation_error"
    assert expected_message in body["message"]


def test_read_existing_task(client: FlaskClient) -> None:
    created = create_task(client, "Read me", 2)

    response = client.get(f"/tasks/{created['id']}", headers=auth_headers())

    assert response.status_code == 200
    task = response.get_json()["task"]
    assert task == created


def test_update_existing_task(client: FlaskClient) -> None:
    created = create_task(client, "Initial", 1)

    response = client.put(
        f"/tasks/{created['id']}",
        json={"description": "Updated", "priority": 5, "due_date": future_date(10)},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    task = response.get_json()["task"]
    assert task["id"] == created["id"]
    assert task["description"] == "Updated"
    assert task["priority"] == 5
    assert task["due_date"] == future_date(10)


def test_delete_existing_task(client: FlaskClient) -> None:
    created = create_task(client, "Delete me", 1)

    delete_response = client.delete(f"/tasks/{created['id']}", headers=auth_headers())
    get_response = client.get(f"/tasks/{created['id']}", headers=auth_headers())

    assert delete_response.status_code == 200
    assert delete_response.get_json()["id"] == created["id"]
    assert get_response.status_code == 404


def test_list_tasks_filter_and_sort(client: FlaskClient) -> None:
    create_task(client, "Low priority later", 1, future_date(10))
    create_task(client, "High priority sooner", 5, future_date(3))
    create_task(client, "High priority later", 5, future_date(20))

    filtered_response = client.get("/tasks?priority=5&sort=due_date&order=desc", headers=auth_headers())

    assert filtered_response.status_code == 200
    tasks = filtered_response.get_json()["tasks"]
    assert [task["description"] for task in tasks] == [
        "High priority later",
        "High priority sooner",
    ]
    assert all(task["priority"] == 5 for task in tasks)


def test_bearer_token_authentication(client: FlaskClient) -> None:
    response = client.get("/tasks", headers={"Authorization": f"Bearer {API_KEY}"})

    assert response.status_code == 200
    assert response.get_json() == {"tasks": []}


def test_concurrent_task_creation_maintains_integrity(tmp_path: Path) -> None:
    database_path = tmp_path / "concurrent.db"
    app = create_app({"TESTING": True, "DATABASE": str(database_path), "API_KEY": API_KEY})

    def post_task(index: int) -> int:
        with app.test_client() as local_client:
            response = local_client.post(
                "/tasks",
                json={
                    "description": f"Concurrent task {index}",
                    "priority": (index % 5) + 1,
                    "due_date": future_date(index + 1),
                },
                headers=auth_headers(),
            )
            assert response.status_code == 201
            return int(response.get_json()["task"]["id"])

    with ThreadPoolExecutor(max_workers=8) as executor:
        ids = list(executor.map(post_task, range(20)))

    assert len(ids) == 20
    assert len(set(ids)) == 20

    with app.test_client() as local_client:
        response = local_client.get("/tasks", headers=auth_headers())

    assert response.status_code == 200
    assert len(response.get_json()["tasks"]) == 20
