import pytest
from pydantic import ValidationError

from notes.schemas import NoteInput


def test_note_input_valid():
    note = NoteInput(title="Hello", body="World")
    assert note.title == "Hello"
    assert note.body == "World"


def test_note_input_strips_whitespace():
    note = NoteInput(title="  Trimmed  ", body="  body  ")
    assert note.title == "Trimmed"
    assert note.body == "body"


def test_note_input_blank_title_raises():
    with pytest.raises(ValidationError) as exc_info:
        NoteInput(title="   ", body="some body")
    assert "blank" in str(exc_info.value).lower()


def test_note_input_missing_title_raises():
    with pytest.raises(ValidationError):
        NoteInput(body="no title")


def test_note_input_body_defaults_to_empty():
    note = NoteInput(title="No body note")
    assert note.body == ""
