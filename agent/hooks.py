import json
import time
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "tool_calls.log"


def log_pre(tool_name: str, tool_input: dict) -> float:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start = time.monotonic()
    line = f"[{timestamp}] PRE  | tool={tool_name} | input={json.dumps(tool_input)}\n"
    existing = LOG_FILE.read_text() if LOG_FILE.exists() else ""
    LOG_FILE.write_text(existing + line)
    return start


def log_post(tool_name: str, result: str, start: float) -> None:
    duration = round(time.monotonic() - start, 2)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_len = len(result)
    line = f"[{timestamp}] POST | tool={tool_name} | dur={duration}s | len={output_len}\n"
    existing = LOG_FILE.read_text() if LOG_FILE.exists() else ""
    LOG_FILE.write_text(existing + line)
