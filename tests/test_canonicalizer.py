import pytest

from app.discovery.canonicalizer import DiscoveryCanonicalizer


def test_canonicalizer_builds_lookup_recipe() -> None:
    history = [
        {
            "step": 1,
            "decision": {
                "type": "click",
                "target": "index_9",
                "reason": "Open the member record",
            },
        },
        {
            "step": 2,
            "decision": {
                "type": "done",
                "target": None,
                "reason": "The member balance is visible",
            },
        },
    ]

    recipe = DiscoveryCanonicalizer().canonicalize(
        "Look up a member and return their current savings balance",
        history,
    )

    assert recipe.artifact_id == "lookup_member_balance"
    assert "member_id" in recipe.inputs
    assert recipe.success.checkpoint == "extract_balance"


def test_canonicalizer_rejects_incomplete_discovery() -> None:
    history = [
        {
            "step": 1,
            "decision": {
                "type": "click",
                "target": "index_9",
                "reason": "Open the member record",
            },
        }
    ]

    with pytest.raises(ValueError, match="did not reach a completed goal state"):
        DiscoveryCanonicalizer().canonicalize(
            "Look up a member and return their current savings balance",
            history,
        )
