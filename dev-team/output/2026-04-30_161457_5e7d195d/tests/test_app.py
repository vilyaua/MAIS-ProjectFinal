import unittest
import json
from src.app import app

class BookApiTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_create_book_success(self):
        book_data = {"title": "Test Book", "author": "Test Author", "year": 2020, "isbn": "1234567890"}
        response = self.client.post('/books', json=book_data)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["title"], "Test Book")
        self.assertEqual(data["author"], "Test Author")

    def test_create_book_invalid_data(self):
        # Missing title
        book_data = {"author": "Test Author"}
        response = self.client.post('/books', json=book_data)
        self.assertEqual(response.status_code, 400)

    def test_get_books_no_filter(self):
        # Create a book first
        book_data = {"title": "Alpha", "author": "Author1"}
        self.client.post('/books', json=book_data)
        response = self.client.get('/books')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(isinstance(data, list))
        self.assertTrue(len(data) > 0)

    def test_get_books_with_filters(self):
        self.client.post('/books', json={"title": "FilterTitle", "author": "FilterAuthor"})
        response = self.client.get('/books?title=filtertitle')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(all("filtertitle" in b["title"].lower() for b in data))

        response = self.client.get('/books?author=filterauthor')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(all("filterauthor" in b["author"].lower() for b in data))

    def test_get_book_found_and_not_found(self):
        # Create book
        book_data = {"title": "FindMe", "author": "AuthorX"}
        response = self.client.post('/books', json=book_data)
        book_id = response.get_json()["id"]

        get_response = self.client.get(f'/books/{book_id}')
        self.assertEqual(get_response.status_code, 200)
        data = get_response.get_json()
        self.assertEqual(data["title"], "FindMe")

        not_found_response = self.client.get('/books/99999')
        self.assertEqual(not_found_response.status_code, 404)

    def test_update_book_success_and_not_found(self):
        # Create book
        book_data = {"title": "ToUpdate", "author": "AuthorY"}
        response = self.client.post('/books', json=book_data)
        book_id = response.get_json()["id"]

        update_data = {"title": "UpdatedTitle"}
        update_response = self.client.put(f'/books/{book_id}', json=update_data)
        self.assertEqual(update_response.status_code, 200)
        updated_book = update_response.get_json()
        self.assertEqual(updated_book["title"], "UpdatedTitle")

        not_found_response = self.client.put('/books/99999', json=update_data)
        self.assertEqual(not_found_response.status_code, 404)

    def test_delete_book_success_and_not_found(self):
        # Create book
        book_data = {"title": "ToDelete", "author": "AuthorZ"}
        response = self.client.post('/books', json=book_data)
        book_id = response.get_json()["id"]

        delete_response = self.client.delete(f'/books/{book_id}')
        self.assertEqual(delete_response.status_code, 204)

        not_found_response = self.client.delete(f'/books/{book_id}')
        self.assertEqual(not_found_response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
