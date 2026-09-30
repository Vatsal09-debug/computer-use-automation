from typing import Protocol

from pydantic import BaseModel


class LLMDecision(BaseModel):
    type: str
    target: str | None = None
    value: str | None = None
    key: str | None = None
    reason: str


class LLMProvider(Protocol):
    async def decide(
        self,
        goal: str,
        observation: dict[str, object],
        history: list[dict[str, object]],
    ) -> LLMDecision:
        ...
