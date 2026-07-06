from decouple import config
from serpapi import GoogleSearch

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


def web_search(query: str, count: int = 5) -> str:
    api_key = config("SERPAPI_KEY", default="")
    if not api_key:
        return "Error: SERPAPI_KEY not set in environment."

    try:
        search = GoogleSearch({"q": query, "api_key": api_key, "num": count})
        results = search.get_dict().get("organic_results", [])
    except Exception as exc:
        return f"Error fetching search results: {exc}"

    if not results:
        return "No results found."

    lines = []
    for item in results:
        title = item.get("title", "No title")
        url = item.get("link", "")
        snippet = item.get("snippet", "")
        lines.append(f"- {title}\n  URL: {url}\n  {snippet}")

    return "\n\n".join(lines)
