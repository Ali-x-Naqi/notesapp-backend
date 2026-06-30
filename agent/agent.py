import json
import sys

from decouple import config
from groq import Groq

from agent.memory import SessionMemory
from agent.skills.web_search import WEB_SEARCH_TOOL, web_search

MAX_ITERATIONS = 5
MODEL = "llama-3.3-70b-versatile"


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
                tools=[WEB_SEARCH_TOOL],
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
                args = json.loads(tool_call.function.arguments)
                result = web_search(args.get("query", ""))
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
