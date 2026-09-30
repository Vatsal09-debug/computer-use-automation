from decimal import Decimal

from app.artifact.actions import (
    AssertAction,
    ClickAction,
    ExtractAction,
    FillAction,
    PressKeyAction,
    WaitAction,
)
from app.artifact.schema import Recipe
from app.evidence.logger import EvidenceLogger
from app.hitl.manager import HandoffManager
from app.replay.result import FailureDetail, ReplayResult
from app.replay.surface import PlaywrightSurface


class ReplaySession:
    """Owns replay state across an optional human handoff."""

    def __init__(
        self,
        recipe: Recipe,
        inputs: dict[str, object],
        surface: PlaywrightSurface,
        handoff_before: set[str] | None = None,
    ) -> None:
        self.recipe = recipe
        self.inputs = inputs
        self.surface = surface
        self.handoff_before = handoff_before or set()
        self.handoff = HandoffManager()
        self.logger = EvidenceLogger()
        self.current_action_index = 0
        self.outputs: dict[str, object] = {}
        self.paused = False

    async def run(self) -> ReplayResult:
        while self.current_action_index < len(self.recipe.actions):
            action = self.recipe.actions[self.current_action_index]

            if self.should_handoff(action.id):
                return self.request_handoff(
                    action.id,
                    f"Human intervention required before action '{action.id}'",
                )

            await self._execute_action(action)
            self.current_action_index += 1

            if action.id == self.recipe.success.checkpoint:
                return ReplayResult(
                    status="success",
                    outputs=self.outputs,
                )

        return ReplayResult(
            status="failure",
            failure=FailureDetail(
                category="checkpoint_not_reached",
                step_id=self.recipe.success.checkpoint,
                expected="Success checkpoint is reached",
                observed="Recipe completed without reaching the checkpoint",
            ),
        )

    async def resume(self) -> ReplayResult:
        if self.handoff.request is None:
            raise RuntimeError("No handoff is pending")

        if self.handoff.request.status != "pending":
            raise RuntimeError("Human handoff is not pending")

        self.handoff.resume()
        self.paused = False

        self.logger.log(
            {
                "event": "human_handoff_resumed",
                "step_id": self.handoff.request.step_id,
            }
        )

        return await self.run()

    async def _execute_action(self, action: object) -> None:
        if isinstance(action, FillAction):
            await self.surface.fill(
                action.target,
                self._resolve_value(action.value),
            )
        elif isinstance(action, ClickAction):
            await self.surface.click(action.target)
        elif isinstance(action, PressKeyAction):
            if action.target is None:
                await self.surface.page.keyboard.press(action.key)
            else:
                await self.surface.press(action.target, action.key)
        elif isinstance(action, WaitAction):
            await self.surface.wait_visible(
                action.target,
                action.timeout_ms,
            )
        elif isinstance(action, AssertAction):
            observed = await self.surface.read_text(action.target)
            expected = self._resolve_value(action.expected)

            if action.assertion == "text_equals":
                passed = observed == expected
            else:
                passed = expected in observed

            if not passed:
                raise ValueError(
                    f"Assertion failed: expected '{expected}', observed '{observed}'"
                )
        elif isinstance(action, ExtractAction):
            observed = await self.surface.read_text(action.target)
            output_type = self.recipe.outputs[action.output].type
            self.outputs[action.output] = self._parse_output(
                output_type,
                observed,
            )

    def should_handoff(self, step_id: str) -> bool:
        return step_id in self.handoff_before and not self.paused

    def request_handoff(
        self,
        step_id: str,
        reason: str,
    ) -> ReplayResult:
        self.handoff.request_handoff(step_id, reason)
        self.paused = True

        self.logger.log(
            {
                "event": "human_handoff_requested",
                "step_id": step_id,
                "reason": reason,
            }
        )

        return ReplayResult(
            status="needs_human",
            failure=FailureDetail(
                category="human_handoff",
                step_id=step_id,
                expected="Human completes the requested interaction",
                observed=reason,
            ),
        )

    def record_human_action(
        self,
        action: str,
        target: str | None = None,
    ) -> None:
        self.handoff.record_human_action(action, target)

        self.logger.log(
            {
                "event": "human_action",
                "action": action,
                "target": target,
            }
        )

        # The handoff action itself is the action that the automation
        # deliberately paused before, so resume from the following step.
        self.current_action_index += 1

    def _resolve_value(self, value: str) -> str:
        import re

        pattern = r"\{\{([^{}]+)\}\}"

        def replace(match: re.Match[str]) -> str:
            name = match.group(1).strip()
            if name not in self.inputs:
                raise ValueError(
                    f"Missing input referenced by action: {name}"
                )
            return str(self.inputs[name])

        return re.sub(pattern, replace, value)

    @staticmethod
    def _parse_output(value_type: str, value: str) -> object:
        if value_type == "money":
            normalized = (
                value.replace("$", "")
                .replace(",", "")
                .strip()
            )
            return Decimal(normalized)

        if value_type == "integer":
            return int(value.strip())

        if value_type == "boolean":
            return value.strip().lower() == "true"

        return value.strip()
