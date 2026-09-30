import json
from pathlib import Path


class EvidenceLogger:
    def __init__(self, root: str = "evidence") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "replay.jsonl"

    def log(self, event: dict[str, object]) -> None:
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, default=str) + "\n")
