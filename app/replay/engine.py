import re
from decimal import Decimal

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.artifact.actions import (
    AssertAction,
    ClickAction,
    ExtractAction,
    FillAction,
    PressKeyAction,
    WaitAction,
)
from app.artifact.schema import Recipe
from app.replay.result import FailureDetail, ReplayResult
from app.replay.surface import PlaywrightSurface
from app.evidence.recorder import EvidenceRecorder
from app.evidence.logger import EvidenceLogger
from app.safety.policy import SafetyPolicy


class ReplayEngine:
    def __init__(
        self,
        surface: PlaywrightSurface,
        safety_policy: SafetyPolicy | None = None,
    ) -> None:
        self.surface = surface
        self.evidence = EvidenceRecorder()
        self.logger = EvidenceLogger()
        self.safety = safety_policy or SafetyPolicy()

    async def run(
        self,
        recipe: Recipe,
        inputs: dict[str, object],
    ) -> ReplayResult:
        try:
            self._validate_inputs(recipe, inputs)

            try:
                self.safety.check_url(self.surface.page.url)
            except PermissionError as exc:
                self.logger.log(
                    {
                        "event": "replay_stopped",
                        "status": "failure",
                        "step_id": "replay_start",
                        "category": "safety_blocked",
                        "expected": "Current page origin is allowed",
                        "observed": str(exc),
                    }
                )
                return ReplayResult(
                    status="failure",
                    failure=FailureDetail(
                        category="safety_blocked",
                        step_id="replay_start",
                        expected="Current page origin is allowed",
                        observed=str(exc),
                    ),
                )

            outputs: dict[str, object] = {}

            for action in recipe.actions:
                try:
                    self.safety.check_action(action.type)
                except PermissionError as exc:
                    self.logger.log(
                        {
                            "event": "replay_stopped",
                            "status": "failure",
                            "step_id": action.id,
                            "category": "safety_blocked",
                            "expected": "Action is allowed by the safety policy",
                            "observed": str(exc),
                        }
                    )
                    return ReplayResult(
                        status="failure",
                        failure=FailureDetail(
                            category="safety_blocked",
                            step_id=action.id,
                            expected="Action is allowed by the safety policy",
                            observed=str(exc),
                        ),
                    )

                self.logger.log(
                    {
                        "event": "action_started",
                        "step_id": action.id,
                        "action": action.type,
                    }
                )

                try:
                    if isinstance(action, FillAction):
                        await self.surface.fill(
                            action.target,
                            self._resolve_value(action.value, inputs),
                        )

                    elif isinstance(action, ClickAction):
                        await self.surface.click(action.target)

                        if action.id == "search_member":
                            search_error = self.surface.resolve(
                                type(action.target)(
                                    id="search_error",
                                    strategy="test_id",
                                    value="search-error",
                                    robustness="Stable application-provided test identifier for the search outcome message.",
                                )
                            )

                            try:
                                await search_error.wait_for(
                                    state="visible",
                                    timeout=1000,
                                )
                            except PlaywrightTimeoutError:
                                pass

                            if await search_error.is_visible():
                                observed = (await search_error.inner_text()).strip()

                                self.logger.log(
                                    {
                                        "event": "replay_stopped",
                                        "status": "business_outcome",
                                        "step_id": action.id,
                                        "category": "member_not_found",
                                        "expected": "Member record exists",
                                        "observed": observed,
                                    }
                                )
                                return ReplayResult(
                                    status="business_outcome",
                                    failure=FailureDetail(
                                        category="member_not_found",
                                        step_id=action.id,
                                        expected="Member record exists",
                                        observed=observed,
                                    ),
                                )

                    elif isinstance(action, PressKeyAction):
                        target = action.target

                        if target is None:
                            await self.surface.page.keyboard.press(action.key)
                        else:
                            await self.surface.press(target, action.key)

                    elif isinstance(action, WaitAction):
                        try:
                            await self.surface.wait_visible(
                                action.target,
                                action.timeout_ms,
                            )
                        except PlaywrightTimeoutError as first_error:
                            try:
                                await self.surface.wait_visible(
                                    action.target,
                                    action.timeout_ms,
                                )
                            except PlaywrightTimeoutError:
                                self.logger.log(
                                    {
                                        "event": "replay_stopped",
                                        "status": "recoverable",
                                        "step_id": action.id,
                                        "category": "transient_timeout",
                                        "expected": "Target becomes visible within the configured timeout",
                                        "observed": str(first_error),
                                    }
                                )
                                return ReplayResult(
                                    status="recoverable",
                                    failure=FailureDetail(
                                        category="transient_timeout",
                                        step_id=action.id,
                                        expected="Target becomes visible within the configured timeout",
                                        observed=str(first_error),
                                    ),
                                )

                    elif isinstance(action, AssertAction):
                        observed = await self.surface.read_text(action.target)
                        expected = self._resolve_value(action.expected, inputs)

                        if action.assertion == "text_equals":
                            passed = observed == expected
                        else:
                            passed = expected in observed

                        if not passed:
                            self.logger.log(
                                {
                                    "event": "replay_stopped",
                                    "status": "failure",
                                    "step_id": action.id,
                                    "category": "assertion_mismatch",
                                    "expected": expected,
                                    "observed": observed,
                                }
                            )
                            return ReplayResult(
                                status="failure",
                                failure=FailureDetail(
                                    category="assertion_mismatch",
                                    step_id=action.id,
                                    expected=expected,
                                    observed=observed,
                                ),
                            )

                    elif isinstance(action, ExtractAction):
                        observed = await self.surface.read_text(action.target)
                        outputs[action.output] = self._parse_output(
                            recipe.outputs[action.output].type,
                            observed,
                        )

                except Exception as exc:
                    evidence_path = await self.evidence.capture_screenshot(
                        self.surface.page,
                        f"failure-{action.id}",
                    )
                    self.logger.log(
                        {
                            "event": "replay_stopped",
                            "status": "failure",
                            "step_id": action.id,
                            "category": "execution_error",
                            "expected": f"Action {action.type} completes successfully",
                            "observed": str(exc),
                            "evidence": evidence_path,
                        }
                    )
                    return ReplayResult(
                        status="failure",
                        failure=FailureDetail(
                            category="execution_error",
                            step_id=action.id,
                            expected=f"Action {action.type} completes successfully",
                            observed=str(exc),
                            evidence=evidence_path,
                        ),
                    )

                self.logger.log(
                    {
                        "event": "action_completed",
                        "step_id": action.id,
                        "action": action.type,
                        "status": "success",
                    }
                )

                if action.id == recipe.success.checkpoint:
                    self.logger.log(
                        {
                            "event": "replay_completed",
                            "status": "success",
                            "checkpoint": action.id,
                        }
                    )
                    return ReplayResult(
                        status="success",
                        outputs=outputs,
                    )

            return ReplayResult(
                status="failure",
                failure=FailureDetail(
                    category="checkpoint_not_reached",
                    step_id=recipe.success.checkpoint,
                    expected="Success checkpoint is reached",
                    observed="Recipe completed without reaching the checkpoint",
                ),
            )

        except ValueError as exc:
            return ReplayResult(
                status="failure",
                failure=FailureDetail(
                    category="invalid_input",
                    step_id="input_validation",
                    expected="All required recipe inputs are provided",
                    observed=str(exc),
                ),
            )

    @staticmethod
    def _validate_inputs(recipe: Recipe, inputs: dict[str, object]) -> None:
        for name, spec in recipe.inputs.items():
            if spec.required and (
                name not in inputs
                or inputs[name] is None
                or inputs[name] == ""
            ):
                raise ValueError(f"Missing required input: {name}")

    @staticmethod
    def _resolve_value(value: str, inputs: dict[str, object]) -> str:
        pattern = r"\{\{([^{}]+)\}\}"

        def replace(match: re.Match[str]) -> str:
            name = match.group(1).strip()

            if name not in inputs:
                raise ValueError(f"Missing input referenced by action: {name}")

            return str(inputs[name])

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
            return int(value)

        if value_type == "boolean":
            normalized = value.lower()

            if normalized == "true":
                return True

            if normalized == "false":
                return False

            raise ValueError(f"Cannot parse boolean output: {value}")

        return value
