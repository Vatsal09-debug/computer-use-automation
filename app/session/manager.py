import os
import uuid
from dataclasses import dataclass

from playwright.async_api import Browser, BrowserContext, Page, Playwright

from app.replay.surface import PlaywrightSurface


@dataclass
class BrowserSession:
    session_id: str
    browser: Browser
    context: BrowserContext
    page: Page
    surface: PlaywrightSurface


class SessionManager:
    def __init__(self, playwright: Playwright) -> None:
        self.playwright = playwright
        self.sessions: dict[str, BrowserSession] = {}
        self.northstar_url = os.getenv(
            "NORTHSTAR_URL",
            "http://localhost:5173",
        )

    async def create(self) -> BrowserSession:
        session_id = str(uuid.uuid4())

        executable_path = os.getenv("PLAYWRIGHT_EXECUTABLE_PATH") or None

        browser = await self.playwright.chromium.launch(
            headless=True,
            executable_path=executable_path,
        )

        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(self.northstar_url)

        session = BrowserSession(
            session_id=session_id,
            browser=browser,
            context=context,
            page=page,
            surface=PlaywrightSurface(page),
        )

        self.sessions[session_id] = session

        return session

    def get(self, session_id: str) -> BrowserSession:
        if session_id not in self.sessions:
            raise KeyError(f"Unknown session: {session_id}")

        return self.sessions[session_id]

    async def close(self, session_id: str) -> None:
        session = self.get(session_id)

        await session.context.close()
        await session.browser.close()

        del self.sessions[session_id]
