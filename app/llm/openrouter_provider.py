import ast
import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.llm.provider import LLMDecision


class OpenRouterProvider:
    def __init__(self) -> None:
        load_dotenv(".env")

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:5173",
                "X-Title": "Computer-Use Automation",
            },
        )

    async def decide(
        self,
        goal: str,
        observation: dict[str, object],
        history: list[dict[str, object]],
    ) -> LLMDecision:
        response = await self.client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a computer-use discovery agent. "
                        "Choose exactly one next UI action toward the user's goal. "
                        "Use only targets present in the observation. "
                        "Allowed actions are: click, fill, press_key, wait, assert, extract, done. "
                        "Do not invent targets. "
                        "Return ONLY valid JSON with these fields: "
                        "type, target, value, key, reason. "
                        "If the goal is complete, use type='done'."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Goal: {goal}\n\n"
                        f"Current observation:\n{observation}\n\n"
                        f"Previous actions:\n{history}"
                    ),
                },
            ],
            temperature=0,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("LLM returned no decision")

        cleaned = content.strip()

        # Accept strict JSON first.
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Some free models return Python-style dict syntax.
            try:
                data = ast.literal_eval(cleaned)
            except (ValueError, SyntaxError) as exc:
                raise RuntimeError(
                    f"LLM returned an unsupported decision format: {content}"
                ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                f"LLM decision must be an object, got: {type(data).__name__}"
            )

        return LLMDecision.model_validate(data)
