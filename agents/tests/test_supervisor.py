import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agents.supervisor import SupervisorAgent


def _make_choice(finish_reason, content=None, tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(finish_reason=finish_reason, message=message)


def _make_tool_call(call_id, name, arguments):
    fn = SimpleNamespace(name=name, arguments=json.dumps(arguments))
    return SimpleNamespace(id=call_id, function=fn)


@patch("agents.supervisor.config", return_value="fake-groq-key")
@patch("agents.supervisor.Groq")
def test_supervisor_returns_answer_without_routing(mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[_make_choice("stop", content="Hi there!")]
    )

    supervisor = SupervisorAgent()
    result = supervisor.run("Say hello")

    assert result == "Hi there!"


@patch("agents.supervisor.config", return_value="fake-groq-key")
@patch("agents.supervisor.Groq")
@patch("agents.supervisor.research_worker", return_value="The capital of France is Paris.")
def test_supervisor_routes_to_research_worker(mock_research, mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    tool_call = _make_tool_call(
        "call_1", "research_worker", {"question": "What is the capital of France?"}
    )
    first = MagicMock(choices=[_make_choice("tool_calls", tool_calls=[tool_call])])
    first.choices[0].message.tool_calls = [tool_call]
    second = MagicMock(choices=[_make_choice("stop", content="The capital of France is Paris.")])

    mock_client.chat.completions.create.side_effect = [first, second]

    supervisor = SupervisorAgent()
    result = supervisor.run("What is the capital of France?")

    assert "Paris" in result
    mock_research.assert_called_once_with("What is the capital of France?")


@patch("agents.supervisor.config", return_value="fake-groq-key")
@patch("agents.supervisor.Groq")
@patch("agents.supervisor.notes_worker", return_value="Created note 1: 'Groceries' for alice.")
def test_supervisor_routes_to_notes_worker(mock_notes, mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    tool_call = _make_tool_call(
        "call_2",
        "notes_worker",
        {"action": "create", "username": "alice", "title": "Groceries", "body": "Milk"},
    )
    first = MagicMock(choices=[_make_choice("tool_calls", tool_calls=[tool_call])])
    first.choices[0].message.tool_calls = [tool_call]
    second = MagicMock(
        choices=[_make_choice("stop", content="Created a note titled 'Groceries' for alice.")]
    )

    mock_client.chat.completions.create.side_effect = [first, second]

    supervisor = SupervisorAgent()
    result = supervisor.run("Create a note called Groceries with body Milk for alice")

    assert "alice" in result
    mock_notes.assert_called_once_with(
        action="create", username="alice", title="Groceries", body="Milk"
    )


@patch("agents.supervisor.config", return_value="fake-groq-key")
@patch("agents.supervisor.Groq")
def test_supervisor_respects_max_iterations(mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    tool_call = _make_tool_call("call_x", "research_worker", {"question": "loop"})
    choice = MagicMock(choices=[_make_choice("tool_calls", tool_calls=[tool_call])])
    choice.choices[0].message.tool_calls = [tool_call]

    with patch("agents.supervisor.research_worker", return_value="some result"):
        mock_client.chat.completions.create.return_value = choice
        supervisor = SupervisorAgent()
        result = supervisor.run("Infinite loop question")

    assert "maximum iterations" in result
