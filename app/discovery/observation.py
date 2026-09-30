from typing import Any

from playwright.async_api import Page


class ObservationBuilder:
    async def build(self, page: Page) -> dict[str, Any]:
        elements = await page.locator(
            "button:visible, a:visible, input:visible, textarea:visible, select:visible"
        ).evaluate_all(
            """
            elements => elements.map((element, index) => {
                const testId = element.getAttribute("data-testid") || "";
                return {
                    index,
                    target: testId || `index_${index}`,
                    tag: element.tagName.toLowerCase(),
                    role: element.getAttribute("role") || "",
                    test_id: testId,
                    text: (
                        element.innerText ||
                        element.getAttribute("aria-label") ||
                        element.getAttribute("placeholder") ||
                        ""
                    ).trim(),
                    value: element.value || ""
                };
            })
            """
        )

        return {
            "url": page.url,
            "title": await page.title(),
            "elements": elements,
        }
