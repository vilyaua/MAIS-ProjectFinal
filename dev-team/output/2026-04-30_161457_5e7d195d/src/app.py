from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException
import html
import re

app = Flask(__name__)

# In-memory storage for books
data_store = {}
current_id = 1

# Helper function to sanitize input

def sanitize_input(value: str) -> str:
    # Escape HTML entities to prevent HTML/JS injection
    safe_value = html.escape(value.strip())
    # You can add more sanitization rules here as needed
    return safe_value

# Validation function for book data

def validate_book_data(data: dict, partial: bool = False) -> tuple[bool, dict]:
    errors = {}

    if not isinstance(data, dict):
        return False, {"error": "Invalid JSON data"}

    # title is required unless partial update
    if not partial or (partial and "title" in data):
        title = data.get("title")
        if not title or not isinstance(title, str) or not title.strip():
            errors["title"] = "Title is required and must be a non-empty string."

    # author is required unless partial update
    if not partial or (partial and "author" in data):
        author = data.get("author")
        if not author or not isinstance(author, str) or not author.strip():
            errors["author"] = "Author is required and must be a non-empty string."

    # Optional fields check (if provided)
    if "year" in data:
        year = data["year"]
        if not (isinstance(year, int) and (0 <= year <= 9999)):
            errors["year"] = "Year must be an integer between 0 and 9999."

    if "isbn" in data:
        isbn = data["isbn"]
        if not (isinstance(isbn, str) and isbn.strip()):
            errors["isbn"] = "ISBN must be a non-empty string if provided."

    return (len(errors) == 0), errors

# Error handlers

@app.errorhandler(400)
def bad_request(e):
    response = {"error": "Bad Request", "message": str(e.description) if isinstance(e, HTTPException) else str(e)}
    return jsonify(response), 400

@app.errorhandler(404)
def not_found(e):
    response = {"error": "Not Found", "message": str(e.description) if isinstance(e, HTTPException) else str(e)}
    return jsonify(response), 404

@app.errorhandler(500)
def internal_error(e):
    response = {"error": "Internal Server Error", "message": "An unexpected error occurred."}
    return jsonify(response), 500

# Routes

@app.route('/books', methods=['POST'])
def create_book():
    global current_id
    if not request.is_json:
        abort(400, description="Request must be JSON")

    data = request.get_json()
    valid, errors = validate_book_data(data)
    if not valid:
        abort(400, description=errors)

    # Sanitize input
    title = sanitize_input(data["title"])
    author = sanitize_input(data["author"])
    year = data.get("year")
    isbn = sanitize_input(data["isbn"]) if "isbn" in data else None

    book = {"id": current_id, "title": title, "author": author}
    if year is not None:
        book["year"] = year
    if isbn is not None:
        book["isbn"] = isbn

    data_store[current_id] = book
    current_id += 1

    response = jsonify(book)
    response.status_code = 201
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/books', methods=['GET'])
def get_books():
    title_filter = request.args.get('title', '').strip().lower()
    author_filter = request.args.get('author', '').strip().lower()

    filtered_books = []
    for book in data_store.values():
        title_matches = title_filter in book['title'].lower() if title_filter else True
        author_matches = author_filter in book['author'].lower() if author_filter else True
        if title_matches and author_matches:
            filtered_books.append(book)

    response = jsonify(filtered_books)
    response.status_code = 200
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id: int):
    book = data_store.get(book_id)
    if not book:
        abort(404, description=f"Book with id {book_id} not found.")

    response = jsonify(book)
    response.status_code = 200
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id: int):
    if not request.is_json:
        abort(400, description="Request must be JSON")

    book = data_store.get(book_id)
    if not book:
        abort(404, description=f"Book with id {book_id} not found.")

    data = request.get_json()
    valid, errors = validate_book_data(data, partial=True)
    if not valid:
        abort(400, description=errors)

    # Update fields if present
    if "title" in data:
        book["title"] = sanitize_input(data["title"])
    if "author" in data:
        book["author"] = sanitize_input(data["author"])
    if "year" in data:
        book["year"] = data["year"]
    if "isbn" in data:
        book["isbn"] = sanitize_input(data["isbn"])

    data_store[book_id] = book

    response = jsonify(book)
    response.status_code = 200
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id: int):
    if book_id not in data_store:
        abort(404, description=f"Book with id {book_id} not found.")

    del data_store[book_id]
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
