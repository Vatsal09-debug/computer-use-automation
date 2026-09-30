from typing import Any

from playwright.async_api import Page


class ObservationBuilder:
    async def build(self, page: Page) -> dict[str, Any]:
        elements = await page.locator(
            "[data-testid]:visible, button:visible, a:visible, input:visible, textarea:visible, select:visible"
        ).evaluate_all(
            """
            elements => elements.map((element, index) => {
                const testId = element.getAttribute("data-testid") || "";
                const text = (
                    element.innerText ||
                    element.getAttribute("aria-label") ||
                    element.getAttribute("placeholder") ||
                    ""
                ).trim();
                return {
                    index,
                    target: testId || `text:${text}`,
                    tag: element.tagName.toLowerCase(),
                    role: element.getAttribute("role") || "",
                    test_id: testId,
                    text,
                    value: element.value || ""
                };
            })
            """
        )

        visible_text = await page.locator("body").inner_text()

        return {
            "url": page.url,
            "title": await page.title(),
            "elements": elements,
            "visible_text": visible_text.strip(),
        }
