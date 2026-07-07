import json
import uuid

from decouple import config
from groq import Groq

from agent.hooks import log_post, log_pre
from agents.workers.notes_worker import NOTES_WORKER_TOOL, notes_worker
from agents.workers.research_worker import RESEARCH_WORKER_TOOL, research_worker

MAX_ITERATIONS = 5
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

WORKER_TOOLS = [RESEARCH_WORKER_TOOL, NOTES_WORKER_TOOL]

WORKER_FUNCTIONS = {
    "research_worker": lambda args, run_id: research_worker(
        args.get("question", ""), run_id=run_id
    ),
    "notes_worker": lambda args, run_id: notes_worker(
        action=args.get("action", ""),
        username=args.get("username", ""),
        title=args.get("title", ""),
        body=args.get("body", ""),
    ),
}

SYSTEM_PROMPT = (
    "You are a supervisor that routes tasks to specialized workers. "
    "Use research_worker for general knowledge questions that need web search "
    "or file reading. Use notes_worker for creating or listing notes."
)


class SupervisorAgent:
    def __init__(self) -> None:
        self.client = Groq(api_key=config("GROQ_API_KEY"))
        self.last_run_id: str | None = None

    def run(self, task: str) -> str:
        run_id = uuid.uuid4().hex[:8]
        self.last_run_id = run_id

        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ]

        for _ in range(MAX_ITERATIONS):
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=WORKER_TOOLS,
                tool_choice="auto",
            )

            choice = response.choices[0]

            if choice.finish_reason == "stop":
                return choice.message.content or ""

            if choice.finish_reason != "tool_calls":
                return choice.message.content or ""

            tool_calls = choice.message.tool_calls or []
            messages.append(choice.message)

            for tool_call in tool_calls:
                args = json.loads(tool_call.function.arguments)
                worker_fn = WORKER_FUNCTIONS.get(tool_call.function.name)
                start = log_pre(
                    tool_call.function.name, args, run_id=run_id, agent_name="supervisor"
                )
                result = (
                    worker_fn(args, run_id)
                    if worker_fn is not None
                    else f"Error: unknown worker '{tool_call.function.name}'"
                )
                log_post(
                    tool_call.function.name,
                    result,
                    start,
                    run_id=run_id,
                    agent_name="supervisor",
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

        return "Reached maximum iterations without a final answer."
