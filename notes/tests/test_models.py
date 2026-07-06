import pytest

from notes.models import Note


@pytest.mark.django_db
def test_note_str_returns_title():
    note = Note.objects.create(title="My Note", body="Some body text")
    assert str(note) == "My Note"


@pytest.mark.django_db
def test_note_default_ordering_is_newest_first():
    Note.objects.create(title="First", body="")
    Note.objects.create(title="Second", body="")
    titles = list(Note.objects.values_list("title", flat=True))
    assert titles == ["Second", "First"]


@pytest.mark.django_db
def test_note_body_can_be_blank():
    note = Note.objects.create(title="No body")
    assert note.body == ""


@pytest.mark.django_db
def test_note_timestamps_are_set_on_create():
    note = Note.objects.create(title="Timestamps")
    assert note.created_at is not None
    assert note.updated_at is not None
