import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent.skills.web_search import web_search
from agent.agent import ResearchAgent


def _make_choice(finish_reason, content=None, tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(finish_reason=finish_reason, message=message)


def _make_tool_call(call_id, name, arguments):
    fn = SimpleNamespace(name=name, arguments=json.dumps(arguments))
    return SimpleNamespace(id=call_id, function=fn)


# --- web_search tests ---


def test_web_search_returns_formatted_results():
    mock_search_instance = MagicMock()
    mock_search_instance.get_dict.return_value = {
        "organic_results": [
            {
                "title": "Example Title",
                "link": "https://example.com",
                "snippet": "An example result.",
            }
        ]
    }

    with patch("agent.skills.web_search.GoogleSearch", return_value=mock_search_instance):
        with patch("agent.skills.web_search.config", return_value="fake-key"):
            result = web_search("test query")

    assert "Example Title" in result
    assert "https://example.com" in result
    assert "An example result." in result


def test_web_search_handles_api_error():
    mock_search_instance = MagicMock()
    mock_search_instance.get_dict.side_effect = Exception("connection error")

    with patch("agent.skills.web_search.GoogleSearch", return_value=mock_search_instance):
        with patch("agent.skills.web_search.config", return_value="fake-key"):
            result = web_search("test query")

    assert "Error" in result


def test_web_search_missing_api_key():
    with patch("agent.skills.web_search.config", return_value=""):
        result = web_search("test query")

    assert "SERPAPI_KEY" in result


# --- ResearchAgent tests ---


@patch("agent.agent.config", return_value="fake-groq-key")
@patch("agent.agent.Groq")
def test_agent_returns_answer_without_tool(mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[_make_choice("stop", content="Paris is the capital of France.")]
    )

    agent = ResearchAgent()
    result = agent.run("What is the capital of France?")

    assert result == "Paris is the capital of France."
    assert mock_client.chat.completions.create.call_count == 1


@patch("agent.agent.config", return_value="fake-groq-key")
@patch("agent.agent.Groq")
@patch("agent.agent.web_search", return_value="Result: OpenAI CEO is Sam Altman.")
def test_agent_calls_web_search_tool(mock_search, mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    tool_call = _make_tool_call("call_1", "web_search", {"query": "OpenAI CEO"})
    first = MagicMock(choices=[_make_choice("tool_calls", tool_calls=[tool_call])])
    first.choices[0].message.tool_calls = [tool_call]
    second = MagicMock(choices=[_make_choice("stop", content="The CEO of OpenAI is Sam Altman.")])

    mock_client.chat.completions.create.side_effect = [first, second]

    agent = ResearchAgent()
    result = agent.run("Who is the CEO of OpenAI?")

    assert "Sam Altman" in result
    mock_search.assert_called_once_with("OpenAI CEO")


@patch("agent.agent.config", return_value="fake-groq-key")
@patch("agent.agent.Groq")
def test_agent_respects_max_iterations(mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    tool_call = _make_tool_call("call_x", "web_search", {"query": "loop"})
    choice = MagicMock(choices=[_make_choice("tool_calls", tool_calls=[tool_call])])
    choice.choices[0].message.tool_calls = [tool_call]

    with patch("agent.agent.web_search", return_value="some result"):
        mock_client.chat.completions.create.return_value = choice
        agent = ResearchAgent()
        result = agent.run("Infinite loop question")

    assert "maximum iterations" in result
