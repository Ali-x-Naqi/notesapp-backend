from pathlib import Path

from agent.agent import ResearchAgent
from agent.hooks import LOG_FILE
from agent.memory import SessionMemory

SAMPLE_FILE = Path(__file__).parent / "sample_topic.txt"


def main() -> None:
    SAMPLE_FILE.write_text(
        "The topic for today's research is: the Groq LPU chip.",
        encoding="utf-8",
    )

    memory = SessionMemory()
    agent = ResearchAgent(memory=memory)

    question = (
        f"Read the file at {SAMPLE_FILE} to find out what topic to research, "
        "then search the web for the latest news on that topic, and summarize "
        "what you find in two sentences."
    )

    answer = agent.run(question)

    print("=== Final Answer ===")
    print(answer)

    print("\n=== Memory after run ===")
    print(memory.get_context())

    print("\n=== Tool call log ===")
    if LOG_FILE.exists():
        print(LOG_FILE.read_text())


if __name__ == "__main__":
    main()
