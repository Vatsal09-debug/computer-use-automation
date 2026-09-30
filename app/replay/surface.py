from playwright.async_api import Locator, Page

from app.artifact.actions import TargetSpec


class PlaywrightSurface:
    def __init__(self, page: Page) -> None:
        self.page = page

    def resolve(self, target: TargetSpec) -> Locator:
        if target.strategy == "test_id":
            return self.page.get_by_test_id(target.value)

        raise ValueError(f"Unsupported target strategy: {target.strategy}")

    async def fill(self, target: TargetSpec, value: str) -> None:
        await self.resolve(target).fill(value)

    async def click(self, target: TargetSpec) -> None:
        await self.resolve(target).click()

    async def press(self, target: TargetSpec, key: str) -> None:
        await self.resolve(target).press(key)

    async def wait_visible(self, target: TargetSpec, timeout_ms: int) -> None:
        await self.resolve(target).wait_for(
            state="visible",
            timeout=timeout_ms,
        )

    async def read_text(self, target: TargetSpec) -> str:
        return (await self.resolve(target).inner_text()).strip()

    async def is_visible(self, target: TargetSpec) -> bool:
        return await self.resolve(target).is_visible()
