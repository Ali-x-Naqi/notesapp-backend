from unittest.mock import patch

from agent.hooks import log_post, log_pre
from agents.tracing import get_trace, parse_log


def test_parse_log_empty_when_file_missing(tmp_path):
    missing = tmp_path / "missing.log"

    assert parse_log(missing) == []


def test_parse_log_parses_lines_without_run_id(tmp_path):
    log_file = tmp_path / "tool_calls.log"
    with patch("agent.hooks.LOG_FILE", log_file):
        start = log_pre("web_search", {"query": "Django"})
        log_post("web_search", "some result", start)

    entries = parse_log(log_file)

    assert len(entries) == 2
    assert entries[0]["phase"] == "PRE"
    assert entries[0]["tool"] == "web_search"
    assert entries[0]["run_id"] is None


def test_get_trace_filters_by_run_id_across_calls(tmp_path):
    log_file = tmp_path / "tool_calls.log"
    with patch("agent.hooks.LOG_FILE", log_file):
        start_a1 = log_pre("research_worker", {"question": "x"}, run_id="run-a")
        log_post("research_worker", "answer", start_a1, run_id="run-a")
        start_b1 = log_pre("notes_worker", {"action": "list"}, run_id="run-b")
        log_post("notes_worker", "[]", start_b1, run_id="run-b")
        start_a2 = log_pre("web_search", {"query": "nested call"}, run_id="run-a")
        log_post("web_search", "nested result", start_a2, run_id="run-a")

    trace_a = get_trace("run-a", log_file)
    trace_b = get_trace("run-b", log_file)

    assert len(trace_a) == 4
    assert all(entry["run_id"] == "run-a" for entry in trace_a)
    assert [entry["tool"] for entry in trace_a] == [
        "research_worker",
        "research_worker",
        "web_search",
        "web_search",
    ]
    assert len(trace_b) == 2
    assert all(entry["tool"] == "notes_worker" for entry in trace_b)


def test_get_trace_returns_empty_for_unknown_run_id(tmp_path):
    log_file = tmp_path / "tool_calls.log"
    with patch("agent.hooks.LOG_FILE", log_file):
        start = log_pre("research_worker", {"question": "x"}, run_id="run-a")
        log_post("research_worker", "answer", start, run_id="run-a")

    assert get_trace("nonexistent", log_file) == []
