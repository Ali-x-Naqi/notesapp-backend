import json

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from notes.models import Note


@pytest.fixture
def note():
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
    assert response.json()["title"][0] == "This field is required."


@pytest.mark.django_db
def test_create_note_whitespace_only_title_returns_400(client):
    # DRF's CharField rejects this before validate_title ever runs (allow_blank=False
    # + trim_whitespace=True are defaults since the model has no blank=True) - so the
    # error is DRF's own message, not our custom "Title cannot be blank." string.
    payload = {"title": "   ", "body": "x"}
    response = client.post(
        reverse("note-list"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json()["title"][0] == "This field may not be blank."


@pytest.mark.django_db
def test_create_note_unauthenticated_sets_user_to_null(client):
    payload = {"title": "Anonymous note"}
    response = client.post(
        reverse("note-list"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["user"] is None


@pytest.mark.django_db
def test_create_note_authenticated_attributes_user(client):
    user = User.objects.create_user(username="carol", password="pw")
    client.force_login(user)

    payload = {"title": "Carol's note"}
    response = client.post(
        reverse("note-list"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["user"] == user.pk


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
    original_created_at = note.created_at

    payload = {"title": "Updated", "body": "Updated body"}
    response = client.put(
        reverse("note-detail", args=[note.pk]),
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    note.refresh_from_db()
    assert note.created_at == original_created_at
    assert note.updated_at > original_created_at


@pytest.mark.django_db
def test_update_note_missing_title_returns_400(client, note):
    payload = {"body": "No title on full update"}
    response = client.put(
        reverse("note-detail", args=[note.pk]),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "title" in response.json()


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
