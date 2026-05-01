"""Flask implementation of a Book Collection Management REST API."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import BadRequest


@dataclass(slots=True)
class Book:
    """A book record stored by the API."""

    id: int
    title: str
    author: str
    publication_year: int
    isbn: str


class BookRepository:
    """Simple in-memory repository for book records."""

    def __init__(self) -> None:
        self._books: dict[int, Book] = {}
        self._next_id = 1

    def create(self, data: dict[str, Any]) -> Book:
        book = Book(id=self._next_id, **data)
        self._books[book.id] = book
        self._next_id += 1
        return book

    def get(self, book_id: int) -> Book | None:
        return self._books.get(book_id)

    def list(self, title: str | None = None, author: str | None = None) -> list[Book]:
        books = list(self._books.values())
        if title is not None:
            normalized_title = title.casefold()
            books = [book for book in books if normalized_title in book.title.casefold()]
        if author is not None:
            normalized_author = author.casefold()
            books = [book for book in books if normalized_author in book.author.casefold()]
        return books

    def update(self, book_id: int, data: dict[str, Any]) -> Book | None:
        if book_id not in self._books:
            return None
        book = Book(id=book_id, **data)
        self._books[book_id] = book
        return book

    def delete(self, book_id: int) -> bool:
        if book_id not in self._books:
            return False
        del self._books[book_id]
        return True


ISBN_ALLOWED_PATTERN = re.compile(r"^(?:ISBN(?:-1[03])?:?\s*)?[0-9Xx][0-9Xx\-\s]{8,20}[0-9Xx]$")


def create_app() -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__)
    repository = BookRepository()

    @app.errorhandler(404)
    def handle_not_found(_: Exception) -> tuple[Response, int]:
        return jsonify({"error": "The requested resource was not found."}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_: Exception) -> tuple[Response, int]:
        return jsonify({"error": "The HTTP method is not allowed for this endpoint."}), 405

    @app.get("/health")
    def health() -> tuple[Response, int]:
        return jsonify({"status": "ok"}), 200

    @app.post("/books")
    def create_book() -> tuple[Response, int]:
        payload = parse_json_body()
        if isinstance(payload, tuple):
            return payload

        validated, errors = validate_book_payload(payload)
        if errors:
            return validation_error(errors)

        book = repository.create(validated)
        return jsonify(book_to_dict(book)), 201

    @app.get("/books")
    def list_books() -> tuple[Response, int]:
        title = request.args.get("title")
        author = request.args.get("author")
        books = repository.list(title=title, author=author)
        return jsonify([book_to_dict(book) for book in books]), 200

    @app.get("/books/<int:book_id>")
    def get_book(book_id: int) -> tuple[Response, int]:
        book = repository.get(book_id)
        if book is None:
            return jsonify({"error": f"Book with id {book_id} was not found."}), 404
        return jsonify(book_to_dict(book)), 200

    @app.put("/books/<int:book_id>")
    def update_book(book_id: int) -> tuple[Response, int]:
        payload = parse_json_body()
        if isinstance(payload, tuple):
            return payload

        validated, errors = validate_book_payload(payload)
        if errors:
            return validation_error(errors)

        book = repository.update(book_id, validated)
        if book is None:
            return jsonify({"error": f"Book with id {book_id} was not found."}), 404
        return jsonify(book_to_dict(book)), 200

    @app.delete("/books/<int:book_id>")
    def delete_book(book_id: int) -> tuple[Response, int]:
        deleted = repository.delete(book_id)
        if not deleted:
            return jsonify({"error": f"Book with id {book_id} was not found."}), 404
        return jsonify({"message": f"Book with id {book_id} was deleted."}), 200

    return app


def parse_json_body() -> dict[str, Any] | tuple[Response, int]:
    """Parse a request JSON body and return a 400 response for malformed input."""

    try:
        payload = request.get_json(force=False, silent=False)
    except BadRequest:
        return jsonify({"error": "Malformed JSON request body."}), 400

    if payload is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON request body must be an object."}), 400
    return payload


def validate_book_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a book payload for create and update requests."""

    errors: list[str] = []
    validated: dict[str, Any] = {}

    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title is required and must be a non-empty string.")
    else:
        validated["title"] = title.strip()

    author = payload.get("author")
    if not isinstance(author, str) or not author.strip():
        errors.append("author is required and must be a non-empty string.")
    else:
        validated["author"] = author.strip()

    year_value = payload.get("publication_year", payload.get("year"))
    if isinstance(year_value, bool) or not isinstance(year_value, int):
        errors.append("publication_year is required and must be a valid integer.")
    else:
        validated["publication_year"] = year_value

    isbn = payload.get("isbn")
    if not isinstance(isbn, str) or not isbn.strip():
        errors.append("isbn is required and must be a valid ISBN-10 or ISBN-13 string.")
    elif not is_valid_isbn(isbn):
        errors.append("isbn must be a valid ISBN-10 or ISBN-13 format.")
    else:
        validated["isbn"] = isbn.strip()

    return validated, errors


def validation_error(errors: list[str]) -> tuple[Response, int]:
    """Build a consistent validation error response."""

    return jsonify({"error": "Invalid book data.", "details": errors}), 400


def book_to_dict(book: Book) -> dict[str, Any]:
    """Serialize a book dataclass to a JSON-compatible dictionary."""

    return asdict(book)


def is_valid_isbn(value: str) -> bool:
    """Validate the common textual formats for ISBN-10 and ISBN-13 strings."""

    candidate = value.strip()
    if not ISBN_ALLOWED_PATTERN.match(candidate):
        return False

    upper_candidate = candidate.upper()
    for prefix in ("ISBN-13", "ISBN-10", "ISBN"):
        if upper_candidate.startswith(prefix):
            candidate = candidate[len(prefix) :]
            if candidate.startswith(":"):
                candidate = candidate[1:]
            break

    compact = re.sub(r"[\s-]", "", candidate).upper()
    return bool(re.fullmatch(r"\d{9}[\dX]", compact) or re.fullmatch(r"\d{13}", compact))
