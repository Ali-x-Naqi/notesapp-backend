from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Note


class NoteUserRelationshipTests(TestCase):
    def test_note_user_defaults_to_null_without_owner(self):
        note = Note.objects.create(title="Ownerless note")

        self.assertIsNone(note.user)

    def test_deleting_user_sets_note_user_to_null(self):
        user = User.objects.create_user(username="alice", password="pw")
        note = Note.objects.create(title="Alice's note", user=user)

        user.delete()
        note.refresh_from_db()

        self.assertIsNone(note.user)

    def test_note_list_uses_select_related_for_user(self):
        user = User.objects.create_user(username="bob", password="pw")
        Note.objects.create(title="First", user=user)
        Note.objects.create(title="Second", user=user)

        client = APIClient()
        with self.assertNumQueries(1):
            response = client.get("/api/notes/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_post_without_authentication_sets_user_to_null(self):
        client = APIClient()

        response = client.post("/api/notes/", {"title": "Anonymous note"}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["user"])


class NoteValidationAndErrorHandlingTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_post_missing_title_returns_400_with_title_error(self):
        response = self.client.post("/api/notes/", {"body": "x"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.data)

    def test_post_whitespace_only_title_returns_400(self):
        response = self.client.post("/api/notes/", {"title": "   "}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.data)

    def test_post_valid_data_returns_201(self):
        response = self.client.post(
            "/api/notes/", {"title": "Valid note", "body": "hello"}, format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Valid note")

    def test_get_missing_note_returns_404_with_detail(self):
        response = self.client.get("/api/notes/9999/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "Not found.")

    def test_unhandled_exception_returns_generic_500_without_traceback(self):
        with patch(
            "notes.views.Note.objects.select_related",
            side_effect=Exception("boom: something exploded internally"),
        ):
            response = self.client.get("/api/notes/")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data, {"detail": "An unexpected error occurred."})
        self.assertNotIn("boom", str(response.data))
