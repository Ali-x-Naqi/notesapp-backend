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
