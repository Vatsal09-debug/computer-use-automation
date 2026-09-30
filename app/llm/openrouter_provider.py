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
                        "When an element exposes a non-empty test_id, prefer its test_id target over an index_* target because test_id targets are more stable across UI state changes. "
                        "Use observation.visible_text as informational evidence about the current page state. "
                        "Do NOT invent targets. "
                        "Prefer actions that make the workflow reusable for the requested input. "
                        "When the goal provides a value such as a member ID and the page exposes an input "
                        "field for that value, use that input field and its associated action instead of "
                        "clicking a hardcoded demonstration record. "
                        "Do not use demonstration shortcuts when they bypass the requested input parameter. "
                        "NEVER click or use a View demo account, demonstration account, preselected member, or other shortcut that bypasses member ID search. "
                        "For this member lookup workflow, you MUST use the member-id input and the search-member action before declaring the goal complete. "
                        "After the search, you MUST verify that the displayed member matches the requested identifier. The displayed member result and balance are already part of the resulting page state; DO NOT click the member result, member name, or result row just to reach the balance. If savings-balance is visible, extract it directly using the savings-balance target, then declare the goal complete. "
                        "For savings balance extraction, prefer the stable savings-balance test_id target when it is present; never use an index_* target for the final extraction when a stable test_id is available. "
                        "For a lookup or search goal, entering an identifier is not sufficient to complete the goal: "
                        "perform the search action and verify that the resulting state corresponds to the requested "
                        "identifier before using type='done'. Do not treat pre-existing registry/table data as proof "
                        "that a new lookup was completed. "
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

        # Remove an optional Markdown JSON code fence emitted by some models.
        if cleaned.startswith("```") and cleaned.endswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].strip().lower() in {"```json", "```"}:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        # Normalize the model response into our internal LLMDecision contract.
        data = None

        # 1. Strict JSON.
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 2. Python-style dict.
        if data is None:
            try:
                data = ast.literal_eval(cleaned)
            except (ValueError, SyntaxError):
                pass

        # 3. JSON object embedded in prose/Markdown.
        if data is None and "{" in cleaned and "}" in cleaned:
            try:
                start_json = cleaned.index("{")
                end_json = cleaned.rindex("}") + 1
                data = json.loads(cleaned[start_json:end_json])
            except (ValueError, json.JSONDecodeError):
                pass

        # 4. XML-like <tool_call> format.
        if data is None and "<tool_call>" in cleaned and "</tool_call>" in cleaned:
            tool = cleaned.split("<tool_call>", 1)[1]
            tool = tool.split("</tool_call>", 1)[0].strip()

            action_type = tool.split("<arg_key>", 1)[0].strip()
            arguments = {}

            for part in tool.split("<arg_key>")[1:]:
                key, remainder = part.split("</arg_key>", 1)
                value, _ = remainder.split("</arg_value>", 1)
                value = value.split("<arg_value>", 1)[1]
                arguments[key.strip()] = value.strip()

            reason = cleaned.split("<tool_call>", 1)[0].strip()

            data = {
                "type": action_type,
                "target": arguments.get("target"),
                "value": arguments.get("value"),
                "key": arguments.get("key"),
                "reason": reason or f"Execute {action_type}",
            }

        # 5. <|tool_call_start|>[click(target='...', index=7)] format.
        if (
            data is None
            and "<|tool_call_start|>" in cleaned
            and "<|tool_call_end|>" in cleaned
        ):
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

            parsed_arguments = {}

            # Parse key='value' arguments while allowing commas inside quoted values.
            import re

            for match in re.finditer(
                r"(\w+)=(?:'([^']*)'|\"([^\"]*)\")",
            ):
                key = match.group(1)
                value = match.group(2) if match.group(2) is not None else match.group(3)
                parsed_arguments[key] = value

            data = {
                "type": action_type.strip(),
                "target": parsed_arguments.get("target"),
                "value": parsed_arguments.get("value"),
                "key": parsed_arguments.get("key"),
                "reason": f"Execute {action_type.strip()} using the selected target.",
            }

        if data is None:
            raise RuntimeError(
                f"LLM returned an unsupported decision format: {content}"
            )

        if not isinstance(data, dict):
            raise RuntimeError(
                f"LLM decision must be an object, got: {type(data).__name__}"
            )

        return LLMDecision.model_validate(data)
