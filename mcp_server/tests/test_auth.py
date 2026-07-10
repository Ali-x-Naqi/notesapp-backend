from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken

from mcp_server.auth import get_authenticated_user


@pytest.mark.django_db
def test_get_authenticated_user_returns_none_without_token():
    with patch("mcp_server.auth.config", return_value=""):
        assert get_authenticated_user() is None


@pytest.mark.django_db
def test_get_authenticated_user_returns_none_for_invalid_token():
    with patch("mcp_server.auth.config", return_value="not-a-real-jwt"):
        assert get_authenticated_user() is None


@pytest.mark.django_db
def test_get_authenticated_user_returns_user_for_valid_token():
    user = User.objects.create_user(username="dave", password="pw")
    token = str(AccessToken.for_user(user))

    with patch("mcp_server.auth.config", return_value=token):
        result = get_authenticated_user()

    assert result == user


@pytest.mark.django_db
def test_get_authenticated_user_returns_none_if_user_deleted():
    user = User.objects.create_user(username="erin", password="pw")
    token = str(AccessToken.for_user(user))
    user.delete()

    with patch("mcp_server.auth.config", return_value=token):
        assert get_authenticated_user() is None
