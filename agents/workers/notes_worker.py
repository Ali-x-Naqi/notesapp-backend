from mcp_server.server import create_note, notes_list

NOTES_WORKER_TOOL = {
    "type": "function",
    "function": {
        "name": "notes_worker",
        "description": (
            "Delegate a notes-related task: create a note for the authenticated user, "
            "or list their existing notes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "list"],
                    "description": "Which notes action to perform",
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


def notes_worker(action: str, title: str = "", body: str = "") -> str:
    """Acts on behalf of whichever identity MCP_ACCESS_TOKEN resolves to (see
    mcp_server/auth.py) - there is no username argument here on purpose, since
    trusting a free-text identity extracted by the LLM was the security gap
    flagged in review. The caller's identity is bound at the process/environment
    level, not per-request from model-generated text.
    """
    if action == "list":
        return notes_list()

    if action == "create":
        return create_note(title=title, body=body)

    return f"Error: unknown action '{action}'"
