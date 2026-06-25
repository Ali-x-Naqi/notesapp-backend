import json

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

from notes.models import Note


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def note(user):
    return Note.objects.create(title="Test Note", body="Test body", user=user)


@pytest.mark.django_db
def test_list_notes_returns_200(auth_client):
    response = auth_client.get(reverse("note-list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_list_notes_returns_only_own_notes(auth_client, user):
    Note.objects.create(title="Mine", body="", user=user)
    other = User.objects.create_user(username="other", password="pass")
    Note.objects.create(title="Theirs", body="", user=other)
    response = auth_client.get(reverse("note-list"))
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_create_note_returns_201(auth_client):
    payload = {"title": "New Note", "body": "Hello"}
    response = auth_client.post(
        reverse("note-list"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["title"] == "New Note"


@pytest.mark.django_db
def test_create_note_missing_title_returns_400(auth_client):
    payload = {"body": "No title here"}
    response = auth_client.post(
        reverse("note-list"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "title" in response.json()


@pytest.mark.django_db
def test_unauthenticated_request_returns_401(client):
    response = client.get(reverse("note-list"))
    assert response.status_code == 401


@pytest.mark.django_db
def test_retrieve_note_returns_200(auth_client, note):
    response = auth_client.get(reverse("note-detail", args=[note.pk]))
    assert response.status_code == 200
    assert response.json()["id"] == note.pk


@pytest.mark.django_db
def test_retrieve_missing_note_returns_404(auth_client):
    response = auth_client.get(reverse("note-detail", args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_note_returns_200(auth_client, note):
    payload = {"title": "Updated", "body": "Updated body"}
    response = auth_client.put(
        reverse("note-detail", args=[note.pk]),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


@pytest.mark.django_db
def test_partial_update_note_returns_200(auth_client, note):
    payload = {"title": "Patched title"}
    response = auth_client.patch(
        reverse("note-detail", args=[note.pk]),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Patched title"


@pytest.mark.django_db
def test_delete_note_returns_204(auth_client, note):
    response = auth_client.delete(reverse("note-detail", args=[note.pk]))
    assert response.status_code == 204
    assert not Note.objects.filter(pk=note.pk).exists()


@pytest.mark.django_db
def test_delete_missing_note_returns_404(auth_client):
    response = auth_client.delete(reverse("note-detail", args=[9999]))
    assert response.status_code == 404
