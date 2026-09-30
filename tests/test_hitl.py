import pytest
from playwright.async_api import async_playwright

from app.artifact.factory import build_lookup_member_balance_recipe
from app.replay.session import ReplaySession
from app.replay.surface import PlaywrightSurface


@pytest.mark.asyncio
async def test_human_takes_over_same_live_session() -> None:
    recipe = build_lookup_member_balance_recipe()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
        page = await browser.new_page()
        await page.goto("http://localhost:5173")

        session = ReplaySession(
            recipe=recipe,
            inputs={"member_id": "12345"},
            surface=PlaywrightSurface(page),
            handoff_before={"search_member"},
        )

        paused = await session.run()

        assert paused.status == "needs_human"
        assert paused.failure is not None
        assert paused.failure.category == "human_handoff"
        assert paused.failure.step_id == "search_member"

        # Human operates on the SAME live Playwright page.
        await page.get_by_test_id("search-member").click()

        session.record_human_action(
            action="click",
            target="search-member",
        )

        resumed = await session.resume()

        await browser.close()

    assert resumed.status == "success"
    assert str(resumed.outputs["savings_balance"]) == "4250.00"
    assert session.handoff.request is not None
    assert session.handoff.request.status == "resumed"
    assert session.handoff.request.human_actions == [
        {
            "action": "click",
            "target": "search-member",
        }
    ]
