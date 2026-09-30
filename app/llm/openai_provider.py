import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.llm.provider import LLMDecision


class OpenAIDecision(BaseModel):
    type: str
    target: str | None = None
    value: str | None = None
    key: str | None = None
    reason: str


class OpenAIProvider:
    def __init__(self) -> None:
        load_dotenv(".env")
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        self.client = AsyncOpenAI(api_key=api_key)

    async def decide(
        self,
        goal: str,
        observation: dict[str, object],
        history: list[dict[str, object]],
    ) -> LLMDecision:
        response = await self.client.responses.parse(
            model="gpt-5.6-luna",
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a computer-use discovery agent. "
                        "Choose exactly one next UI action toward the user's goal. "
                        "Use only targets present in the observation. "
                        "Allowed actions are: click, fill, press_key, wait, assert, extract, done. "
                        "Do not invent targets. "
                        "If the goal is complete, return type='done'."
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
            text_format=OpenAIDecision,
        )

        decision = response.output_parsed

        if decision is None:
            raise RuntimeError("LLM returned no structured decision")

        return LLMDecision.model_validate(decision.model_dump())
