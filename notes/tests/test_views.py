import json

import pytest
from django.urls import reverse

from notes.models import Note


@pytest.fixture
def note(db):
    return Note.objects.create(title="Test Note", body="Test body")


@pytest.mark.django_db
def test_list_notes_returns_200(client):
    response = client.get(reverse("note-list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_list_notes_returns_all_notes(client):
    Note.objects.create(title="A")
    Note.objects.create(title="B")
    response = client.get(reverse("note-list"))
    assert len(response.json()) == 2


@pytest.mark.django_db
def test_create_note_returns_201(client):
    payload = {"title": "New Note", "body": "Hello"}
    response = client.post(
        reverse("note-list"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["title"] == "New Note"


@pytest.mark.django_db
def test_create_note_missing_title_returns_400(client):
    payload = {"body": "No title here"}
    response = client.post(
        reverse("note-list"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "title" in response.json()


@pytest.mark.django_db
def test_retrieve_note_returns_200(client, note):
    response = client.get(reverse("note-detail", args=[note.pk]))
    assert response.status_code == 200
    assert response.json()["id"] == note.pk


@pytest.mark.django_db
def test_retrieve_missing_note_returns_404(client):
    response = client.get(reverse("note-detail", args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_note_returns_200(client, note):
    payload = {"title": "Updated", "body": "Updated body"}
    response = client.put(
        reverse("note-detail", args=[note.pk]),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


@pytest.mark.django_db
def test_partial_update_note_returns_200(client, note):
    payload = {"title": "Patched title"}
    response = client.patch(
        reverse("note-detail", args=[note.pk]),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Patched title"


@pytest.mark.django_db
def test_delete_note_returns_204(client, note):
    response = client.delete(reverse("note-detail", args=[note.pk]))
    assert response.status_code == 204
    assert not Note.objects.filter(pk=note.pk).exists()


@pytest.mark.django_db
def test_delete_missing_note_returns_404(client):
    response = client.delete(reverse("note-detail", args=[9999]))
    assert response.status_code == 404
