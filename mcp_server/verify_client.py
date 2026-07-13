import asyncio
import os

import django
from django.conf import settings as django_settings

if not django_settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notesapp.settings")
    django.setup()

from django.contrib.auth.models import User  # noqa: E402
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402
from rest_framework_simplejwt.tokens import AccessToken  # noqa: E402

DEMO_USERNAME = "mcp_verify_user"


def get_or_create_demo_token() -> str:
    """Runs before the event loop starts — plain sync Django ORM access."""
    user, _ = User.objects.get_or_create(username=DEMO_USERNAME)
    return str(AccessToken.for_user(user))


async def run_client(access_token: str) -> None:
    params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.server"],
        env={**os.environ, "MCP_ACCESS_TOKEN": access_token},
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Connected. Tools:", [t.name for t in tools.tools])

            resources = await session.list_resources()
            print("Resources:", [str(r.uri) for r in resources.resources])

            tool_result = await session.call_tool(
                "create_note",
                {"title": "MCP client verification", "body": "ok"},
            )
            print("Tool result:", tool_result.content[0].text)

            resource_result = await session.read_resource("notes://list")
            print("Resource result (truncated):", resource_result.contents[0].text[:300])


if __name__ == "__main__":
    token = get_or_create_demo_token()
    asyncio.run(run_client(token))
