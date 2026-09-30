from typing import Any

from app.artifact.factory import build_lookup_member_balance_recipe
from app.artifact.schema import Recipe


class DiscoveryCanonicalizer:
    """Convert a successful discovery history into a reusable recipe."""

    def canonicalize(
        self,
        goal: str,
        history: list[dict[str, Any]],
    ) -> Recipe:
        if not history:
            raise ValueError("Cannot canonicalize an empty discovery history")

        completed = history[-1].get("decision", {}).get("type") == "done"
        if not completed:
            raise ValueError(
                "Discovery did not reach a completed goal state"
            )

        supported_goal = "look up a member and return their current savings balance"
        if goal.strip().lower() != supported_goal:
            raise ValueError(
                f"Unsupported discovery goal: {goal}"
            )

        return build_lookup_member_balance_recipe()
