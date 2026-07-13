import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

from notes.models import Note


@pytest.mark.django_db
def test_note_user_defaults_to_null_without_owner():
    note = Note.objects.create(title="Ownerless note")

    assert note.user is None


@pytest.mark.django_db
def test_deleting_user_sets_note_user_to_null():
    user = User.objects.create_user(username="alice", password="pw")
    note = Note.objects.create(title="Alice's note", user=user)

    user.delete()
    note.refresh_from_db()

    assert note.user is None


@pytest.mark.django_db
def test_note_list_uses_select_related_for_user(django_assert_num_queries):
    user = User.objects.create_user(username="bob", password="pw")
    Note.objects.create(title="First", user=user)
    Note.objects.create(title="Second", user=user)

    client = APIClient()
    client.force_authenticate(user=user)

    with django_assert_num_queries(1):
        response = client.get(reverse("note-list"))

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.django_db
def test_post_without_authentication_returns_401(client):
    response = client.post(
        reverse("note-list"),
        data={"title": "Anonymous note"},
        content_type="application/json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_post_authenticated_sets_user_to_requesting_user():
    user = User.objects.create_user(username="carol", password="pw")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        reverse("note-list"),
        data={"title": "Carol's note"},
        content_type="application/json",
    )

    assert response.status_code == 201
    assert response.json()["user"] == user.pk
