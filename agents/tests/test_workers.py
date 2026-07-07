from unittest.mock import patch

from agents.workers.notes_worker import notes_worker
from agents.workers.research_worker import research_worker


def test_research_worker_delegates_to_research_agent():
    with patch("agents.workers.research_worker.ResearchAgent") as mock_agent_cls:
        mock_agent_cls.return_value.run.return_value = "Paris is the capital of France."

        result = research_worker("What is the capital of France?")

    assert result == "Paris is the capital of France."
    mock_agent_cls.return_value.run.assert_called_once_with("What is the capital of France?")


def test_notes_worker_list_action():
    with patch("agents.workers.notes_worker.notes_list", return_value="[]"):
        result = notes_worker(action="list")

    assert result == "[]"


def test_notes_worker_create_action():
    with patch(
        "agents.workers.notes_worker.create_note",
        return_value="Created note 1: 'Groceries' for alice.",
    ) as mock_create:
        result = notes_worker(action="create", username="alice", title="Groceries", body="Milk")

    assert "Created note" in result
    mock_create.assert_called_once_with(username="alice", title="Groceries", body="Milk")


def test_notes_worker_unknown_action():
    result = notes_worker(action="delete")

    assert "unknown action" in result
