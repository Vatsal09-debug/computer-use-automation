import json
from pathlib import Path
from typing import Any


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
            "decision": decision,
            "observation": observation,
        }

        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, default=str) + "\n")
