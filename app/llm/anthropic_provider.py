import json
import os

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from app.llm.provider import LLMDecision


class AnthropicProvider:
    def __init__(self) -> None:
        load_dotenv(".env")

        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")

        self.client = AsyncAnthropic(api_key=api_key)

    async def decide(
        self,
        goal: str,
        observation: dict[str, object],
        history: list[dict[str, object]],
    ) -> LLMDecision:
        system_prompt = """
You are a computer-use discovery agent operating a synthetic enterprise web application.

Your job is to choose exactly ONE next UI action toward the user's goal.

IMPORTANT RULES:
- Use ONLY a target that appears in observation.elements[].target.
- Never invent a target.
- Prefer a target with a non-empty test_id because it is more stable.
- Never use index_* targets when a stable test_id or semantic target is available.
- Use the current observation to determine what is actually visible.
- Use the requested input value from the goal when filling a form.
- Do not use demo accounts, preselected records, or shortcuts that bypass the requested lookup.
- For member lookup, use the member-id input and search-member action.
- After searching, verify the displayed member identifier matches the requested identifier.
- Do NOT click a member result merely to reach the balance.
- When savings-balance appears in observation.elements[].target, you MUST use exactly "savings-balance" as the extract target. Never use a text: target for savings balance extraction.
- Only use type="done" after the requested information has actually been obtained.
- Allowed action types: click, fill, press_key, wait, assert, extract, done.

Return ONLY valid JSON with exactly these fields:

{
  "type": "click|fill|press_key|wait|assert|extract|done",
  "target": "target from observation or null",
  "value": "value or null",
  "key": "key or null",
  "reason": "short explanation"
}
"""

        user_prompt = (
            f"Goal:\n{goal}\n\n"
            f"Current observation:\n{json.dumps(observation, default=str)}\n\n"
            f"Previous actions:\n{json.dumps(history, default=str)}"
        )

        response = await self.client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        )

        content = "".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ).strip()

        print(f"RAW CLAUDE RESPONSE: {content!r}")

        if not content:
            raise RuntimeError("Claude returned no decision")

        if content.startswith("```") and content.endswith("```"):
            lines = content.splitlines()
            if lines and lines[0].strip().lower() in {"```json", "```"}:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Claude returned invalid JSON: {content}"
            ) from exc

        return LLMDecision.model_validate(data)
