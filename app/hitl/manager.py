from dataclasses import dataclass, field
from typing import Any


@dataclass
class HandoffRequest:
    step_id: str
    reason: str
    status: str = "pending"
    human_actions: list[dict[str, Any]] = field(default_factory=list)


class HandoffManager:
    """Coordinates a pause/resume handoff while preserving the live session."""

    def __init__(self) -> None:
        self.request: HandoffRequest | None = None

    def request_handoff(self, step_id: str, reason: str) -> HandoffRequest:
        if self.request is not None and self.request.status == "pending":
            raise RuntimeError("A human handoff is already pending")

        self.request = HandoffRequest(
            step_id=step_id,
            reason=reason,
        )
        return self.request

    def record_human_action(
        self,
        action: str,
        target: str | None = None,
    ) -> None:
        if self.request is None or self.request.status != "pending":
            raise RuntimeError("No pending human handoff")

        self.request.human_actions.append(
            {
                "action": action,
                "target": target,
            }
        )

    def resume(self) -> None:
        if self.request is None or self.request.status != "pending":
            raise RuntimeError("No pending human handoff")

        self.request.status = "resumed"
