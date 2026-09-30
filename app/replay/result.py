from typing import Literal

from pydantic import BaseModel, Field


ReplayStatus = Literal[
    "success",
    "business_outcome",
    "recoverable",
    "needs_human",
    "failure",
]


class FailureDetail(BaseModel):
    category: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    expected: str = Field(min_length=1)
    observed: str = Field(min_length=1)
    evidence: str | None = None


class ReplayResult(BaseModel):
    status: ReplayStatus
    outputs: dict[str, object] = Field(default_factory=dict)
    failure: FailureDetail | None = None
