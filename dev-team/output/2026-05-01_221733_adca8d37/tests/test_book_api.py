from __future__ import annotations

import pytest

from src.book_api import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def valid_book(**overrides):
    data = {
        "title": "The Hobbit",
        "author": "J. R. R. Tolkien",
        "publication_year": 1937,
        "isbn": "978-0-618-00221-3",
    }
    data.update(overrides)
    return data


def create_book(client, **overrides):
    return client.post("/books", json=valid_book(**overrides))


def test_create_book_returns_created_book(client):
    response = create_book(client)

    assert response.status_code == 201
    body = response.get_json()
    assert body["id"] == 1
    assert body["title"] == "The Hobbit"
    assert body["author"] == "J. R. R. Tolkien"
    assert body["publication_year"] == 1937
    assert body["isbn"] == "978-0-618-00221-3"


def test_get_book_by_id_returns_book_or_404(client):
    create_book(client)

    found = client.get("/books/1")
    missing = client.get("/books/999")

    assert found.status_code == 200
    assert found.get_json()["title"] == "The Hobbit"
    assert missing.status_code == 404
    assert "not found" in missing.get_json()["error"].lower()


def test_search_books_by_partial_case_insensitive_title_and_author(client):
    create_book(client, title="Clean Code", author="Robert C. Martin", isbn="9780132350884")
    create_book(client, title="The Clean Coder", author="Robert C. Martin", isbn="978-0-13-708107-3")
    create_book(client, title="Refactoring", author="Martin Fowler", isbn="978-0-201-48567-7")

    response = client.get("/books?title=clean&author=ROBERT")

    assert response.status_code == 200
    body = response.get_json()
    assert [book["title"] for book in body] == ["Clean Code", "The Clean Coder"]


def test_search_with_no_matches_returns_empty_list(client):
    create_book(client)

    response = client.get("/books?title=missing")

    assert response.status_code == 200
    assert response.get_json() == []


@pytest.mark.parametrize(
    "payload, expected_message",
    [
        ({"author": "Author", "publication_year": 2020, "isbn": "9780132350884"}, "title"),
        ({"title": " ", "author": "Author", "publication_year": 2020, "isbn": "9780132350884"}, "title"),
        ({"title": "Title", "publication_year": 2020, "isbn": "9780132350884"}, "author"),
        ({"title": "Title", "author": "Author", "publication_year": "2020", "isbn": "9780132350884"}, "publication_year"),
        ({"title": "Title", "author": "Author", "publication_year": 2020, "isbn": "invalid"}, "isbn"),
    ],
)
def test_create_book_rejects_invalid_input(client, payload, expected_message):
    response = client.post("/books", json=payload)

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "Invalid book data."
    assert any(expected_message in detail for detail in body["details"])


def test_update_book_success_and_not_found(client):
    create_book(client)
    updated_data = valid_book(
        title="The Lord of the Rings",
        publication_year=1954,
        isbn="978-0-618-64015-7",
    )

    updated = client.put("/books/1", json=updated_data)
    missing = client.put("/books/999", json=updated_data)

    assert updated.status_code == 200
    assert updated.get_json()["title"] == "The Lord of the Rings"
    assert updated.get_json()["publication_year"] == 1954
    assert missing.status_code == 404


def test_update_rejects_invalid_input_before_not_found_check(client):
    response = client.put("/books/999", json=valid_book(title=""))

    assert response.status_code == 400
    assert "title" in response.get_json()["details"][0]


def test_delete_book_success_then_not_found_when_already_deleted(client):
    create_book(client)

    deleted = client.delete("/books/1")
    deleted_again = client.delete("/books/1")

    assert deleted.status_code == 200
    assert "deleted" in deleted.get_json()["message"]
    assert deleted_again.status_code == 404


def test_malformed_json_returns_400(client):
    response = client.post("/books", data="{bad json", content_type="application/json")

    assert response.status_code == 400
    assert "json" in response.get_json()["error"].lower()


def test_non_object_json_returns_400(client):
    response = client.post("/books", json=["not", "an", "object"])

    assert response.status_code == 400
    assert "object" in response.get_json()["error"].lower()
