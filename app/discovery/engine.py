from app.discovery.executor import DiscoveryActionExecutor
from app.discovery.observation import ObservationBuilder
from app.discovery.recorder import DiscoveryRecorder
from app.llm.openrouter_provider import OpenRouterProvider
from app.replay.surface import PlaywrightSurface


class DiscoveryEngine:
    def __init__(
        self,
        surface: PlaywrightSurface,
        provider: OpenRouterProvider,
        max_steps: int = 12,
    ) -> None:
        self.surface = surface
        self.provider = provider
        self.max_steps = max_steps
        self.observer = ObservationBuilder()
        self.executor = DiscoveryActionExecutor(surface)
        self.recorder = DiscoveryRecorder()

    async def run(self, goal: str) -> list[dict[str, object]]:
        history: list[dict[str, object]] = []

        for step in range(1, self.max_steps + 1):
            observation = await self.observer.build(self.surface.page)

            decision = await self.provider.decide(
                goal=goal,
                observation=observation,
                history=history,
            )

            event = {
                "step": step,
                "decision": decision.model_dump(),
                "url": self.surface.page.url,
            }

            history.append(event)

            self.recorder.record(
                step=step,
                observation=observation,
                decision=decision.model_dump(),
            )

            print(
                f"Step {step}: "
                f"{decision.type} "
                f"target={decision.target} "
                f"reason={decision.reason}"
            )

            if decision.type == "done":
                return history

            await self.executor.execute(decision, observation)

        raise RuntimeError(
            f"Discovery exceeded maximum of {self.max_steps} steps"
        )
