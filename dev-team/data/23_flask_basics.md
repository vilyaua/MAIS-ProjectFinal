# Flask Web Framework Basics

## Overview

Flask is a lightweight WSGI web framework for Python. Minimal core with extensions for everything else.

## Basic App

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.get("/")
def index():
    return jsonify({"message": "Hello, World!"})

@app.post("/items")
def create_item():
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "name is required"}), 400
    return jsonify({"id": 1, "name": data["name"]}), 201

@app.get("/items/<int:item_id>")
def get_item(item_id):
    return jsonify({"id": item_id, "name": "Example"})

if __name__ == "__main__":
    app.run(debug=True)
```

## Request Data

- `request.get_json()` — parse JSON body
- `request.args.get("key")` — query parameters
- `request.form.get("key")` — form data
- `request.headers.get("Authorization")` — headers

## Error Handling

```python
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request"}), 400
```

## Testing

```python
import pytest

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()

def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
```

## Best Practices

- Use app factory pattern (`create_app()`) for testability
- Return consistent JSON error responses
- Use `@app.get`, `@app.post` decorators (Flask 2.0+)
- Validate all input data
- Use proper HTTP status codes (201, 400, 404, 500)
