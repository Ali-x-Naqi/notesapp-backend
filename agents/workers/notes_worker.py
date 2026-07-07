from mcp_server.server import create_note, notes_list

NOTES_WORKER_TOOL = {
    "type": "function",
    "function": {
        "name": "notes_worker",
        "description": (
            "Delegate a notes-related task: create a note for a user, "
            "or list every existing note."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "list"],
                    "description": "Which notes action to perform",
                },
                "username": {
                    "type": "string",
                    "description": "Username to create the note for (required for 'create')",
                },
                "title": {
                    "type": "string",
                    "description": "Note title (required for 'create')",
                },
                "body": {
                    "type": "string",
                    "description": "Note body (optional for 'create')",
                },
            },
            "required": ["action"],
        },
    },
}


def notes_worker(action: str, username: str = "", title: str = "", body: str = "") -> str:
    if action == "list":
        return notes_list()

    if action == "create":
        return create_note(username=username, title=title, body=body)

    return f"Error: unknown action '{action}'"
