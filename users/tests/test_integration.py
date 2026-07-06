"""
Happy-path integration test: Register -> Login -> Create -> Read -> Update -> Delete.

Uses real SQLite in-memory DB (no mocks). Verifies the complete auth + CRUD lifecycle
in a single test so regressions in any layer surface immediately.
"""

import json

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_full_notes_lifecycle():
    client = APIClient()

    # 1. Register
    register_payload = {
        "username": "integrationuser",
        "email": "int@example.com",
        "password": "intpassword1",
        "password_confirm": "intpassword1",
    }
    reg_response = client.post(
        reverse("auth-register"),
        data=json.dumps(register_payload),
        content_type="application/json",
    )
    assert reg_response.status_code == 201
    access_token = reg_response.json()["access"]

    # 2. Authenticate subsequent requests
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    # 3. Create a note
    create_response = client.post(
        reverse("note-list"),
        data=json.dumps({"title": "Integration Note", "body": "Initial body"}),
        content_type="application/json",
    )
    assert create_response.status_code == 201
    note_id = create_response.json()["id"]
    assert create_response.json()["title"] == "Integration Note"

    # 4. Read the note
    read_response = client.get(reverse("note-detail", args=[note_id]))
    assert read_response.status_code == 200
    assert read_response.json()["body"] == "Initial body"

    # 5. Update the note (PATCH)
    patch_response = client.patch(
        reverse("note-detail", args=[note_id]),
        data=json.dumps({"body": "Updated body"}),
        content_type="application/json",
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["body"] == "Updated body"

    # 6. Delete the note
    delete_response = client.delete(reverse("note-detail", args=[note_id]))
    assert delete_response.status_code == 204

    # 7. Confirm deletion
    confirm_response = client.get(reverse("note-detail", args=[note_id]))
    assert confirm_response.status_code == 404
