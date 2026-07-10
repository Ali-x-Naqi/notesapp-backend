from unittest.mock import patch

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_post_missing_title_returns_400_with_title_error(client):
    response = client.post(reverse("note-list"), {"body": "x"}, content_type="application/json")

    assert response.status_code == 400
    assert "title" in response.json()


@pytest.mark.django_db
def test_post_whitespace_only_title_returns_400(client):
    response = client.post(
        reverse("note-list"), {"title": "   "}, content_type="application/json"
    )

    assert response.status_code == 400
    assert "title" in response.json()


@pytest.mark.django_db
def test_post_valid_data_returns_201(client):
    response = client.post(
        reverse("note-list"),
        {"title": "Valid note", "body": "hello"},
        content_type="application/json",
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Valid note"


@pytest.mark.django_db
def test_get_missing_note_returns_404_with_detail(client):
    response = client.get(reverse("note-detail", args=[9999]))

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found."


@pytest.mark.django_db
def test_unhandled_exception_returns_generic_500_without_traceback(client):
    with patch(
        "notes.views.Note.objects.select_related",
        side_effect=Exception("boom: something exploded internally"),
    ):
        response = client.get(reverse("note-list"))

    assert response.status_code == 500
    assert response.json() == {"detail": "An unexpected error occurred."}
    assert "boom" not in str(response.json())
