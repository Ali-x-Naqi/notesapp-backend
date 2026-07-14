from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent.agent import ResearchAgent
from agent.memory import SessionMemory

# --- SessionMemory unit tests ---


def test_memory_starts_empty():
    mem = SessionMemory()
    assert len(mem) == 0
    assert mem.get_context() == ""


def test_memory_stores_and_recalls_entry():
    mem = SessionMemory()
    mem.add("What is Python?", "Python is a programming language.")
    assert len(mem) == 1
    context = mem.get_context()
    assert "What is Python?" in context
    assert "Python is a programming language." in context


def test_memory_formats_multiple_entries():
    mem = SessionMemory()
    mem.add("Q1", "A1")
    mem.add("Q2", "A2")
    context = mem.get_context()
    assert "1." in context
    assert "2." in context
    assert "Q1" in context
    assert "Q2" in context


def test_memory_clear_resets_state():
    mem = SessionMemory()
    mem.add("Q", "A")
    mem.clear()
    assert len(mem) == 0
    assert mem.get_context() == ""


# --- ResearchAgent + memory integration tests ---


def _make_choice(finish_reason, content=None, tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(finish_reason=finish_reason, message=message)


@patch("agent.agent.config", return_value="fake-groq-key")
@patch("agent.agent.Groq")
def test_agent_stores_answer_in_memory(mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[_make_choice("stop", content="Berlin is the capital of Germany.")]
    )

    mem = SessionMemory()
    agent = ResearchAgent(memory=mem)
    agent.run("What is the capital of Germany?")

    assert len(mem) == 1
    assert "Berlin" in mem.get_context()


@patch("agent.agent.config", return_value="fake-groq-key")
@patch("agent.agent.Groq")
def test_agent_injects_memory_as_system_message(mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[_make_choice("stop", content="Rome is the capital of Italy.")]
    )

    mem = SessionMemory()
    mem.add("What is the capital of France?", "Paris is the capital of France.")

    agent = ResearchAgent(memory=mem)
    agent.run("What is the capital of Italy?")

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs.get("messages") or call_args.args[0]
    system_messages = [m for m in messages if m.get("role") == "system"]

    assert len(system_messages) == 1
    assert "Paris" in system_messages[0]["content"]


@patch("agent.agent.config", return_value="fake-groq-key")
@patch("agent.agent.Groq")
def test_agent_without_memory_sends_no_system_message(mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[_make_choice("stop", content="42")]
    )

    agent = ResearchAgent()
    agent.run("What is 6 times 7?")

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs.get("messages") or call_args.args[0]
    system_messages = [m for m in messages if m.get("role") == "system"]

    assert len(system_messages) == 0


@patch("agent.agent.config", return_value="fake-groq-key")
@patch("agent.agent.Groq")
def test_agent_memory_grows_across_multiple_runs(mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[_make_choice("stop", content="Answer 1")]),
        MagicMock(choices=[_make_choice("stop", content="Answer 2")]),
    ]

    mem = SessionMemory()
    agent = ResearchAgent(memory=mem)
    agent.run("Question 1")
    agent.run("Question 2")

    assert len(mem) == 2


@patch("agent.agent.config", return_value="fake-groq-key")
@patch("agent.agent.Groq")
def test_agent_does_not_store_empty_answer(mock_groq_cls, mock_config):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[_make_choice("stop", content="")]
    )

    mem = SessionMemory()
    agent = ResearchAgent(memory=mem)
    agent.run("Unanswerable question")

    assert len(mem) == 0
