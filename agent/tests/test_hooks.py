import time
from unittest.mock import patch

from agent.hooks import log_post, log_pre


def test_log_pre_writes_pre_line(tmp_path):
    log_file = tmp_path / "tool_calls.log"
    with patch("agent.hooks.LOG_FILE", log_file):
        start = log_pre("web_search", {"query": "Django"})
        content = log_file.read_text()
    assert "PRE" in content
    assert "web_search" in content
    assert '"query": "Django"' in content
    assert isinstance(start, float)


def test_log_post_writes_post_line(tmp_path):
    log_file = tmp_path / "tool_calls.log"
    with patch("agent.hooks.LOG_FILE", log_file):
        start = time.monotonic()
        log_post("web_search", "some result text", start)
        content = log_file.read_text()
    assert "POST" in content
    assert "web_search" in content
    assert "dur=" in content
    assert "len=16" in content


def test_logs_append_not_overwrite(tmp_path):
    log_file = tmp_path / "tool_calls.log"
    with patch("agent.hooks.LOG_FILE", log_file):
        start = log_pre("web_search", {"query": "first"})
        log_post("web_search", "result", start)
        start2 = log_pre("web_search", {"query": "second"})
        log_post("web_search", "result2", start2)
        lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 4


def test_log_pre_includes_run_id_when_provided(tmp_path):
    log_file = tmp_path / "tool_calls.log"
    with patch("agent.hooks.LOG_FILE", log_file):
        log_pre("research_worker", {"question": "x"}, run_id="abc123")
        content = log_file.read_text()
    assert "run=abc123" in content


def test_log_pre_omits_run_id_when_not_provided(tmp_path):
    log_file = tmp_path / "tool_calls.log"
    with patch("agent.hooks.LOG_FILE", log_file):
        log_pre("web_search", {"query": "x"})
        content = log_file.read_text()
    assert "run=" not in content


def test_log_pre_includes_agent_name_when_provided(tmp_path):
    log_file = tmp_path / "tool_calls.log"
    with patch("agent.hooks.LOG_FILE", log_file):
        log_pre("research_worker", {"question": "x"}, agent_name="supervisor")
        content = log_file.read_text()
    assert "agent=supervisor" in content


def test_log_post_includes_agent_name_when_provided(tmp_path):
    log_file = tmp_path / "tool_calls.log"
    with patch("agent.hooks.LOG_FILE", log_file):
        start = time.monotonic()
        log_post("web_search", "result", start, agent_name="research_worker")
        content = log_file.read_text()
    assert "agent=research_worker" in content


def test_log_pre_omits_agent_name_when_not_provided(tmp_path):
    log_file = tmp_path / "tool_calls.log"
    with patch("agent.hooks.LOG_FILE", log_file):
        log_pre("web_search", {"query": "x"})
        content = log_file.read_text()
    assert "agent=" not in content
