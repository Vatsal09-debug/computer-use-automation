from app.llm.provider import LLMDecision
from app.replay.surface import PlaywrightSurface


class DiscoveryActionExecutor:
    def __init__(self, surface: PlaywrightSurface) -> None:
        self.surface = surface

    async def execute(
        self,
        decision: LLMDecision,
        observation: dict[str, object],
    ) -> None:
        if decision.type == "done":
            return

        allowed_types = {
            "click",
            "fill",
            "press_key",
            "wait",
            "assert",
            "extract",
        }

        if decision.type not in allowed_types:
            raise ValueError(f"Unsupported discovery action: {decision.type}")

        if not decision.target:
            raise ValueError(
                f"Discovery action '{decision.type}' requires a target"
            )

        observed_elements = [
            element
            for element in observation["elements"]
            if isinstance(element, dict)
        ]

        target = next(
            (
                element
                for element in observed_elements
                if element.get("target") == decision.target
            ),
            None,
        )

        if target is None:
            raise ValueError(
                f"Target '{decision.target}' is not present in the current observation"
            )

        from app.artifact.actions import TargetSpec

        test_id = target.get("test_id")

        if test_id:
            target_spec = TargetSpec(
                id=decision.target,
                strategy="test_id",
                value=test_id,
                robustness="Target was observed as a visible element with a stable data-testid.",
            )
        else:
            target_spec = None

        if target_spec is not None:
            if decision.type == "click":
                await self.surface.click(target_spec)

            elif decision.type == "fill":
                if decision.value is None:
                    raise ValueError("Fill action requires a value")
                await self.surface.fill(target_spec, decision.value)

            elif decision.type == "press_key":
                if decision.key is None:
                    raise ValueError("Press-key action requires a key")
                await self.surface.press(target_spec, decision.key)

            elif decision.type == "wait":
                await self.surface.wait_visible(target_spec, 5000)

            elif decision.type == "assert":
                if decision.value is None:
                    raise ValueError("Assert action requires an expected value")
                observed_text = await self.surface.read_text(target_spec)
                if decision.value not in observed_text:
                    raise ValueError(
                        f"Assertion failed: expected '{decision.value}', "
                        f"observed '{observed_text}'"
                    )

            elif decision.type == "extract":
                await self.surface.read_text(target_spec)

        else:
            semantic_text = target.get("text", "").strip()
            tag = target.get("tag", "")

            if not semantic_text or not isinstance(tag, str) or not tag:
                raise ValueError(
                    f"Semantic target '{decision.target}' does not contain usable target metadata"
                )

            normalized_target = " ".join(semantic_text.split())

            candidates = self.surface.page.locator(f"{tag}:visible")
            matches = []

            for index in range(await candidates.count()):
                candidate_text = " ".join(
                    (await candidates.nth(index).inner_text()).split()
                )
                if candidate_text == normalized_target:
                    matches.append(candidates.nth(index))

            if len(matches) != 1:
                raise ValueError(
                    f"Semantic target '{decision.target}' did not resolve uniquely "
                    f"from observed tag/text"
                )

            locator = matches[0]

            if decision.type == "click":
                await locator.click()

            elif decision.type == "fill":
                if decision.value is None:
                    raise ValueError("Fill action requires a value")
                await locator.fill(decision.value)

            elif decision.type == "press_key":
                if decision.key is None:
                    raise ValueError("Press-key action requires a key")
                await locator.press(decision.key)

            elif decision.type == "wait":
                await locator.wait_for(state="visible", timeout=5000)

            elif decision.type == "assert":
                if decision.value is None:
                    raise ValueError("Assert action requires an expected value")
                observed_text = (await locator.inner_text()).strip()
                if decision.value not in observed_text:
                    raise ValueError(
                        f"Assertion failed: expected '{decision.value}', "
                        f"observed '{observed_text}'"
                    )

            elif decision.type == "extract":
                await locator.inner_text()
