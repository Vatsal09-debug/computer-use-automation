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
                        "You are a computer-use discovery agent operating a live enterprise UI. "
                        "Choose exactly one next UI action toward the user's goal. "
                        "Use ONLY a target value that appears in observation.elements[].target. "
                        "Use observation.visible_text as informational evidence about the current page state. "
                        "Do NOT invent targets. "
                        "Prefer actions that make the workflow reusable for the requested input rather than "
                        "clicking a hardcoded demonstration record when an input field is available. "
                        "If the goal has been achieved and the required information is visible, use type='done'. "
                        "Allowed actions are: click, fill, press_key, wait, assert, extract, done. "
                        "Return ONLY the decision object. "
                        "Do not return explanations, Markdown, code blocks, or safety commentary. "
                        "The decision must contain exactly these fields: type, target, value, key, reason."
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
            except (ValueError, SyntaxError):
                # Some models emit a tool-call-like wrapper instead of JSON.
                # Extract only the inner action expression; Pydantic below
                # still validates the resulting decision structure.
                prefix = "["
                suffix = "]<|tool_call_end|>"

                if "<|tool_call_start|>" in cleaned and "<|tool_call_end|>" in cleaned:
                    inner = cleaned.split("<|tool_call_start|>", 1)[1]
                    inner = inner.split("<|tool_call_end|>", 1)[0].strip()

                    if inner.startswith("[") and inner.endswith("]"):
                        inner = inner[1:-1].strip()

                    if "(" not in inner or not inner.endswith(")"):
                        raise RuntimeError(
                            f"LLM returned an unsupported decision format: {content}"
                        )

                    action_type, arguments = inner.split("(", 1)
                    arguments = arguments[:-1]

                    data = {"type": action_type.strip()}

                    for part in arguments.split(","):
                        key, value = part.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        if value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        data[key] = value
                else:
                    raise RuntimeError(
                        f"LLM returned an unsupported decision format: {content}"
                    )

        if not isinstance(data, dict):
            raise RuntimeError(
                f"LLM decision must be an object, got: {type(data).__name__}"
            )

        return LLMDecision.model_validate(data)
