import re
from pathlib import Path

from agent.hooks import LOG_FILE

_LINE_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\] (?P<phase>PRE|POST)\s*\| "
    r"(?:run=(?P<run_id>\S+) \| )?(?:agent=(?P<agent>\S+) \| )?"
    r"tool=(?P<tool>\S+) \| (?P<rest>.*)$"
)


def parse_log(log_file: Path | None = None) -> list[dict]:
    """Parse tool_calls.log into a list of structured PRE/POST entries, in file order."""
    path = log_file or LOG_FILE
    if not path.exists():
        return []

    entries = []
    for line in path.read_text().splitlines():
        match = _LINE_RE.match(line)
        if match is None:
            continue
        entries.append(match.groupdict())
    return entries


def get_trace(run_id: str, log_file: Path | None = None) -> list[dict]:
    """Return every PRE/POST entry belonging to one run_id, across every agent that logged one."""
    return [entry for entry in parse_log(log_file) if entry.get("run_id") == run_id]
