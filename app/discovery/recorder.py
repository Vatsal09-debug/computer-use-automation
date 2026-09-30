import json
from pathlib import Path
from typing import Any

from app.evidence.redactor import redact_observation


class DiscoveryRecorder:
    def __init__(self, root: str = "evidence") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "discovery.jsonl"

    def record(
        self,
        step: int,
        observation: dict[str, Any],
        decision: dict[str, Any],
    ) -> None:
        event = {
            "event": "discovery_step",
            "step": step,
            "url": observation.get("url"),
            "decision": {"type": decision.get("type"), "target": decision.get("target"), "value": "[REDACTED_VALUE]" if decision.get("value") else decision.get("value"), "key": "[REDACTED_KEY]" if decision.get("key") else decision.get("key"), "reason": redact_observation({"visible_text": decision.get("reason", "")})["visible_text"],},
            "observation": redact_observation(observation),
        }

        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, default=str) + "\n")

    def record_failure(
        self,
        step: int,
        action: dict[str, Any],
        error: str,
    ) -> None:
        event = {
            "event": "action_failed",
            "step": step,
            "action": {
                "type": action.get("type"),
                "target": action.get("target"),
                "value": "[REDACTED_VALUE]" if action.get("value") else action.get("value"),
                "key": "[REDACTED_KEY]" if action.get("key") else action.get("key"),
                "reason": redact_observation(
                    {"visible_text": action.get("reason", "")}
                )["visible_text"],
            },
            "error": redact_observation({"visible_text": error})["visible_text"],
        }

        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, default=str) + "\n")

