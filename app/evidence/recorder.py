from pathlib import Path

from playwright.async_api import Page


class EvidenceRecorder:
    def __init__(self, root: str = "evidence") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    async def capture_screenshot(self, page: Page, name: str) -> str:
        path = self.root / f"{name}.png"
        await page.screenshot(path=str(path), full_page=True)
        return str(path)
