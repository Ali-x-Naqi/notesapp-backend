import pytest
from pydantic import ValidationError

from users.schemas import RegisterInput


def test_register_input_valid():
    data = RegisterInput(
        username="alice",
        email="alice@example.com",
        password="strongpass1",
        password_confirm="strongpass1",
    )
    assert data.username == "alice"


def test_register_input_passwords_mismatch_raises():
    with pytest.raises(ValidationError) as exc_info:
        RegisterInput(
            username="alice",
            email="alice@example.com",
            password="strongpass1",
            password_confirm="different",
        )
    assert "match" in str(exc_info.value).lower()


def test_register_input_short_password_raises():
    with pytest.raises(ValidationError) as exc_info:
        RegisterInput(
            username="alice",
            email="alice@example.com",
            password="short",
            password_confirm="short",
        )
    assert "8" in str(exc_info.value)


def test_register_input_invalid_email_raises():
    with pytest.raises(ValidationError):
        RegisterInput(
            username="alice",
            email="not-an-email",
            password="strongpass1",
            password_confirm="strongpass1",
        )


def test_register_input_blank_username_raises():
    with pytest.raises(ValidationError) as exc_info:
        RegisterInput(
            username="   ",
            email="alice@example.com",
            password="strongpass1",
            password_confirm="strongpass1",
        )
    assert "blank" in str(exc_info.value).lower()
