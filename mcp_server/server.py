import json
import os

import django
from django.conf import settings as django_settings

if not django_settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notesapp.settings")
    django.setup()

from asgiref.sync import sync_to_async  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402
from pydantic import ValidationError as PydanticValidationError  # noqa: E402

from notes.models import Note  # noqa: E402
from notes.schemas import NoteInput  # noqa: E402

mcp = FastMCP("notesapp-mcp")


def notes_list() -> str:
    """Return every note in the system as a JSON array."""
    notes = Note.objects.select_related("user").all()
    data = [
        {
            "id": note.id,
            "user": note.user.username if note.user else None,
            "title": note.title,
            "body": note.body,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
        }
        for note in notes
    ]
    return json.dumps(data, indent=2)


def create_note(username: str, title: str, body: str = "") -> str:
    """Create a new note owned by the given username."""
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return f"Error: user '{username}' not found."

    try:
        note_input = NoteInput(title=title, body=body)
    except PydanticValidationError as exc:
        return f"Error: {exc}"

    note = Note.objects.create(user=user, title=note_input.title, body=note_input.body)
    return f"Created note {note.id}: '{note.title}' for {username}."


@mcp.resource("notes://list", name="notes_list")
async def notes_list_resource() -> str:
    """MCP-registered resource wrapper: runs the sync ORM call in a worker thread."""
    return await sync_to_async(notes_list, thread_sensitive=True)()


@mcp.tool(name="create_note")
async def create_note_tool(username: str, title: str, body: str = "") -> str:
    """MCP-registered tool wrapper: runs the sync ORM call in a worker thread."""
    return await sync_to_async(create_note, thread_sensitive=True)(
        username=username, title=title, body=body
    )


if __name__ == "__main__":
    mcp.run()
