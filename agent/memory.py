class SessionMemory:
    """Stores question/answer pairs from the current session so the agent can recall prior facts."""

    def __init__(self) -> None:
        self._entries: list[tuple[str, str]] = []

    def add(self, question: str, answer: str) -> None:
        self._entries.append((question, answer))

    def get_context(self) -> str:
        if not self._entries:
            return ""
        lines = ["Earlier in this session you answered the following:"]
        for i, (q, a) in enumerate(self._entries, start=1):
            lines.append(f"{i}. Q: {q}\n   A: {a}")
        return "\n".join(lines)

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)
