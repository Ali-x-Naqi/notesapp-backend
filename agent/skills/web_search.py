from decouple import config
from tavily import TavilyClient

WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for up-to-date information on any topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
            },
            "required": ["query"],
        },
    },
}


def web_search(query: str) -> str:
    api_key = config("TAVILY_API_KEY", default="")
    if not api_key:
        return "Error: TAVILY_API_KEY not set in environment."

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=5)
    except Exception as exc:
        return f"Error fetching search results: {exc}"

    results = response.get("results", [])
    if not results:
        return "No results found."

    lines = []
    for item in results:
        title = item.get("title", "No title")
        url = item.get("url", "")
        content = item.get("content", "")
        lines.append(f"- {title}\n  URL: {url}\n  {content}")

    return "\n\n".join(lines)
