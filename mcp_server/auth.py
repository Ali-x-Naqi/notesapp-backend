from decouple import config
from django.contrib.auth.models import User
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


def get_authenticated_user() -> User | None:
    """Resolve the single Django user this MCP server session is authenticated as.

    Reads a JWT access token (the same kind issued by POST /api/auth/token/)
    from the MCP_ACCESS_TOKEN environment variable, rather than trusting a
    free-text username argument from the MCP client/LLM. Returns None if no
    token is configured, the token is invalid/expired, or the user it names
    no longer exists.
    """
    token_str = config("MCP_ACCESS_TOKEN", default="")
    if not token_str:
        return None

    try:
        token = AccessToken(token_str)
    except TokenError:
        return None

    user_id = token.get("user_id")
    if user_id is None:
        return None

    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None
