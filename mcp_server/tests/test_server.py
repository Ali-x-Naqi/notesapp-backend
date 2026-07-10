import json
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User

from mcp_server.server import NOT_AUTHENTICATED_ERROR, create_note, notes_list
from notes.models import Note


@pytest.mark.django_db
def test_notes_list_requires_authentication():
    with patch("mcp_server.server.get_authenticated_user", return_value=None):
        result = notes_list()

    assert result == NOT_AUTHENTICATED_ERROR


@pytest.mark.django_db
def test_notes_list_returns_only_own_notes_for_regular_user():
    user = User.objects.create_user(username="alice", password="pw")
    other = User.objects.create_user(username="bob", password="pw")
    Note.objects.create(user=user, title="Mine", body="")
    Note.objects.create(user=other, title="Theirs", body="")

    with patch("mcp_server.server.get_authenticated_user", return_value=user):
        result = notes_list()

    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["title"] == "Mine"


@pytest.mark.django_db
def test_notes_list_returns_all_notes_for_admin():
    admin = User.objects.create_user(username="admin", password="pw")
    admin.profile.role = admin.profile.ROLE_ADMIN
    admin.profile.save()
    other = User.objects.create_user(username="bob", password="pw")
    Note.objects.create(user=admin, title="Mine", body="")
    Note.objects.create(user=other, title="Theirs", body="")

    with patch("mcp_server.server.get_authenticated_user", return_value=admin):
        result = notes_list()

    data = json.loads(result)
    assert len(data) == 2


@pytest.mark.django_db
def test_create_note_requires_authentication():
    with patch("mcp_server.server.get_authenticated_user", return_value=None):
        result = create_note(title="Anything")

    assert result == NOT_AUTHENTICATED_ERROR
    assert not Note.objects.exists()


@pytest.mark.django_db
def test_create_note_success_attributes_authenticated_user():
    user = User.objects.create_user(username="carol", password="pw")

    with patch("mcp_server.server.get_authenticated_user", return_value=user):
        result = create_note(title="Shopping list", body="Bread")

    assert "Created note" in result
    assert Note.objects.filter(title="Shopping list", user=user).exists()


@pytest.mark.django_db
def test_create_note_blank_title_returns_pydantic_validation_error():
    user = User.objects.create_user(username="carol", password="pw")

    with patch("mcp_server.server.get_authenticated_user", return_value=user):
        result = create_note(title="   ")

    assert "Title cannot be blank" in result
    assert not Note.objects.exists()
