import re
from typing import Any


_CURRENCY_PATTERN = re.compile(r"\$\s?\d[\d,]*(?:\.\d{2})?")
_ID_PATTERN = re.compile(r"\b\d{5,}\b")
_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def redact_text(value: str) -> str:
    value = _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", value)
    value = _CURRENCY_PATTERN.sub("[REDACTED_AMOUNT]", value)
    value = _ID_PATTERN.sub("[REDACTED_ID]", value)
    return value


def redact_observation(observation: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(observation)

    if isinstance(redacted.get("visible_text"), str):
        redacted["visible_text"] = redact_text(redacted["visible_text"])

    elements = redacted.get("elements")
    if isinstance(elements, list):
        redacted["elements"] = []

        for element in elements:
            if not isinstance(element, dict):
                redacted["elements"].append(element)
                continue

            item = dict(element)

            for key in ("text",):
                if isinstance(item.get(key), str):
                    item[key] = redact_text(item[key])

            if "value" in item:
                item["value"] = "[REDACTED_VALUE]"

            redacted["elements"].append(item)

    return redacted
