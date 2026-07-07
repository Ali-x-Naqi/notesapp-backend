import json

import pytest
from django.contrib.auth.models import User

from mcp_server.server import create_note, notes_list
from notes.models import Note


@pytest.mark.django_db
def test_notes_list_empty():
    result = notes_list()

    assert json.loads(result) == []


@pytest.mark.django_db
def test_notes_list_returns_notes():
    user = User.objects.create_user(username="alice", password="pw")
    Note.objects.create(user=user, title="Groceries", body="Milk, eggs")

    result = notes_list()
    data = json.loads(result)

    assert len(data) == 1
    assert data[0]["title"] == "Groceries"
    assert data[0]["user"] == "alice"


@pytest.mark.django_db
def test_create_note_success():
    User.objects.create_user(username="bob", password="pw")

    result = create_note(username="bob", title="Shopping list", body="Bread")

    assert "Created note" in result
    assert Note.objects.filter(title="Shopping list", user__username="bob").exists()


@pytest.mark.django_db
def test_create_note_unknown_user():
    result = create_note(username="ghost", title="Anything")

    assert "not found" in result
    assert not Note.objects.exists()


@pytest.mark.django_db
def test_create_note_blank_title():
    User.objects.create_user(username="carol", password="pw")

    result = create_note(username="carol", title="   ")

    assert "Error" in result
    assert not Note.objects.exists()
