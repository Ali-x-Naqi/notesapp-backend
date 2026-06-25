import json

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

from notes.models import Note
from users.models import UserProfile


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", password="securepass123")


@pytest.fixture
def admin_user(db):
    u = User.objects.create_user(username="boss", password="adminpass123")
    u.profile.role = UserProfile.ROLE_ADMIN
    u.profile.save()
    return u


@pytest.fixture
def auth_client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def admin_client(admin_user):
    c = APIClient()
    c.force_authenticate(user=admin_user)
    return c


# ── Auth tests ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_register_returns_201_with_tokens(client):
    payload = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "strongpass1",
        "password_confirm": "strongpass1",
    }
    response = client.post(
        reverse("auth-register"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.json()
    assert "access" in data
    assert "refresh" in data


@pytest.mark.django_db
def test_register_passwords_mismatch_returns_400(client):
    payload = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "strongpass1",
        "password_confirm": "differentpass",
    }
    response = client.post(
        reverse("auth-register"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_login_valid_credentials_returns_tokens(client, user):
    payload = {"username": "alice", "password": "securepass123"}
    response = client.post(
        reverse("auth-token"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert "access" in data
    assert "refresh" in data


@pytest.mark.django_db
def test_login_invalid_credentials_returns_401(client):
    payload = {"username": "nobody", "password": "wrongpass"}
    response = client.post(
        reverse("auth-token"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_unauthenticated_notes_access_returns_401(client):
    response = client.get(reverse("note-list"))
    assert response.status_code == 401


# ── CRUD + role tests ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_authenticated_user_can_create_note(auth_client):
    payload = {"title": "My secured note", "body": "content"}
    response = auth_client.post(
        reverse("note-list"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_user_cannot_access_another_users_note(auth_client, admin_user):
    other_note = Note.objects.create(title="Secret", body="", user=admin_user)
    response = auth_client.get(reverse("note-detail", args=[other_note.pk]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_access_any_note(admin_client, user):
    note = Note.objects.create(title="Alice's note", body="", user=user)
    response = admin_client.get(reverse("note-detail", args=[note.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_sees_all_notes_in_list(admin_client, user, admin_user):
    Note.objects.create(title="Alice note", body="", user=user)
    Note.objects.create(title="Admin note", body="", user=admin_user)
    response = admin_client.get(reverse("note-list"))
    assert len(response.json()) == 2


@pytest.mark.django_db
def test_delete_nonexistent_note_returns_404(auth_client):
    response = auth_client.delete(reverse("note-detail", args=[9999]))
    assert response.status_code == 404
