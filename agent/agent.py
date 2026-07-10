import json
import sys

from decouple import config
from groq import Groq

from agent.hooks import log_post, log_pre
from agent.memory import SessionMemory
from agent.skills.file_read import FILE_READ_TOOL, file_read
from agent.skills.web_search import WEB_SEARCH_TOOL, web_search

MAX_ITERATIONS = 5
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

TOOLS = [WEB_SEARCH_TOOL, FILE_READ_TOOL]

TOOL_FUNCTIONS = {
    "web_search": lambda args: web_search(args.get("query", "")),
    "file_read": lambda args: file_read(args.get("path", "")),
}


class ResearchAgent:
    def __init__(self, memory: SessionMemory | None = None) -> None:
        self.client = Groq(api_key=config("GROQ_API_KEY"))
        self.memory = memory

    def run(self, question: str) -> str:
        messages: list[dict] = []

        context = self.memory.get_context() if self.memory is not None else ""
        if context:
            messages.append({"role": "system", "content": context})

        messages.append({"role": "user", "content": question})

        for _ in range(MAX_ITERATIONS):
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            choice = response.choices[0]

            if choice.finish_reason == "stop":
                answer = choice.message.content or ""
                if self.memory is not None and answer:
                    self.memory.add(question, answer)
                return answer

            if choice.finish_reason != "tool_calls":
                return choice.message.content or ""

            tool_calls = choice.message.tool_calls or []
            messages.append(choice.message)

            for tool_call in tool_calls:
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    result = "Error: malformed tool-call arguments (invalid JSON)."
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )
                    continue

                tool_fn = TOOL_FUNCTIONS.get(tool_call.function.name)
                start = log_pre(tool_call.function.name, args)
                result = (
                    tool_fn(args)
                    if tool_fn is not None
                    else f"Error: unknown tool '{tool_call.function.name}'"
                )
                log_post(tool_call.function.name, result, start)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

        return "Reached maximum iterations without a final answer."


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "What is the latest news in AI?"
    agent = ResearchAgent(memory=SessionMemory())
    print(agent.run(question))
