from agent.agent import ResearchAgent
from agent.memory import SessionMemory

RESEARCH_WORKER_TOOL = {
    "type": "function",
    "function": {
        "name": "research_worker",
        "description": (
            "Delegate a general knowledge question to the research worker, "
            "which can search the web and read local files to find an answer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question to research"},
            },
            "required": ["question"],
        },
    },
}


def research_worker(question: str) -> str:
    agent = ResearchAgent(memory=SessionMemory())
    return agent.run(question)
