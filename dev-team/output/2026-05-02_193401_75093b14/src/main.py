"""Convenience entry point for creating the Task Manager API app."""

from app import DEFAULT_API_KEY, create_app

if __name__ == "__main__":
    application = create_app()
    print("Task Manager API initialized.")
    print(f"Development API key: {DEFAULT_API_KEY}")
    print("Use a WSGI server or `flask --app src.app run` to serve the API.")
