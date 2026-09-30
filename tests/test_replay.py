from pathlib import Path
import pytest
from playwright.async_api import async_playwright

from app.artifact.schema import Recipe
from app.replay.engine import ReplayEngine
from app.replay.surface import PlaywrightSurface


@pytest.mark.asyncio
@pytest.mark.parametrize("member_id, expected_status", [
    ("12345", "success"),
    ("99999", "business_outcome"),
])
async def test_lookup_member_balance_replay(
    member_id: str,
    expected_status: str,
) -> None:
    recipe = Recipe.model_validate(
        {
            "artifact_id": "lookup_member_balance",
            "name": "Lookup Member Balance",
            "goal": "Look up a member and return their current savings balance",
            "surface": {
                "type": "web",
                "application": "northstar-banking",
                "version": "1.0",
            },
            "inputs": {
                "member_id": {
                    "type": "string",
                    "required": True,
                    "description": "Northstar member identifier",
                }
            },
            "actions": [
                {
                    "id": "navigate_to_members",
                    "type": "click",
                    "target": {
                        "id": "nav_members",
                        "strategy": "test_id",
                        "value": "nav-members",
                        "robustness": "Stable application-provided test identifier for the primary Members navigation.",
                    },
                },
                {
                    "id": "fill_member_id",
                    "type": "fill",
                    "target": {
                        "id": "member_id",
                        "strategy": "test_id",
                        "value": "member-id",
                        "robustness": "Stable application-provided test identifier.",
                    },
                    "value": "{{member_id}}",
                },
                {
                    "id": "search_member",
                    "type": "click",
                    "target": {
                        "id": "search_member",
                        "strategy": "test_id",
                        "value": "search-member",
                        "robustness": "Stable application-provided test identifier.",
                    },
                },
                {
                    "id": "wait_for_member",
                    "type": "wait",
                    "target": {
                        "id": "member_name",
                        "strategy": "test_id",
                        "value": "member-name",
                        "robustness": "Stable application-provided test identifier.",
                    },
                    "condition": "visible",
                    "timeout_ms": 5000,
                },
                {
                    "id": "verify_member",
                    "type": "assert",
                    "target": {
                        "id": "member_id_result",
                        "strategy": "test_id",
                        "value": "member-id-result",
                        "robustness": "Stable application-provided test identifier.",
                    },
                    "assertion": "text_contains",
                    "expected": "{{member_id}}",
                },
                {
                    "id": "extract_balance",
                    "type": "extract",
                    "target": {
                        "id": "savings_balance",
                        "strategy": "test_id",
                        "value": "savings-balance",
                        "robustness": "Stable application-provided test identifier.",
                    },
                    "output": "savings_balance",
                },
            ],
            "outputs": {
                "savings_balance": {
                    "type": "money",
                    "description": "Current savings account balance",
                }
            },
            "success": {
                "checkpoint": "extract_balance",
            },
        }
    )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
        headless=True,
        executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ) 
        page = await browser.new_page()

        await page.goto("http://localhost:5173")

        engine = ReplayEngine(PlaywrightSurface(page))

        result = await engine.run(
            recipe,
            {"member_id": "12345"},
        )

        await browser.close()

    print(result.model_dump())
    assert result.status == "success"
    print(result.model_dump())
    assert str(result.outputs["savings_balance"]) == "4250.00"


@pytest.mark.asyncio
async def test_replay_wait_timeout_is_recoverable() -> None:
    recipe = Recipe.model_validate(
        {
            "artifact_id": "test_recoverable_wait",
            "name": "Recoverable Wait Test",
            "goal": "Demonstrate bounded recovery from a transient wait timeout",
            "surface": {
                "type": "web",
                "application": "northstar-banking",
                "version": "1.0",
            },
            "inputs": {},
            "actions": [
                {
                    "id": "wait_for_missing_target",
                    "type": "wait",
                    "target": {
                        "id": "temporary_target",
                        "strategy": "test_id",
                        "value": "temporary-target-that-does-not-exist",
                        "robustness": "Controlled test target used to simulate temporary UI unavailability.",
                    },
                    "condition": "visible",
                    "timeout_ms": 100,
                }
            ],
            "outputs": {},
            "success": {
                "checkpoint": "wait_for_missing_target",
            },
        }
    )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
        page = await browser.new_page()
        await page.goto("http://localhost:5173")

        engine = ReplayEngine(PlaywrightSurface(page))

        result = await engine.run(recipe, {})

        await browser.close()

    assert result.status == "recoverable"
    assert result.failure is not None
    assert result.failure.category == "transient_timeout"
    assert result.failure.step_id == "wait_for_missing_target"

@pytest.mark.asyncio
async def test_replay_hard_failure_captures_evidence() -> None:
    recipe = Recipe.model_validate(
        {
            "artifact_id": "test_hard_failure",
            "name": "Hard Failure Test",
            "goal": "Demonstrate evidence capture for a non-recoverable execution error",
            "surface": {
                "type": "web",
                "application": "northstar-banking",
                "version": "1.0",
            },
            "inputs": {},
            "actions": [
                {
                    "id": "click_missing_target",
                    "type": "click",
                    "target": {
                        "id": "missing_target",
                        "strategy": "test_id",
                        "value": "target-that-does-not-exist",
                        "robustness": "Controlled test target used to simulate a hard execution failure.",
                    },
                }
            ],
            "outputs": {},
            "success": {"checkpoint": "click_missing_target"},
        }
    )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
        page = await browser.new_page()
        await page.goto("http://localhost:5173")

        engine = ReplayEngine(PlaywrightSurface(page))
        result = await engine.run(recipe, {})

        await browser.close()

    assert result.status == "failure"
    assert result.failure is not None
    assert result.failure.category == "execution_error"
    assert result.failure.step_id == "click_missing_target"
    assert result.failure.evidence is not None
    assert Path(result.failure.evidence).exists()
