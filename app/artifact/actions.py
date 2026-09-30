from typing import Literal

from pydantic import BaseModel, Field


class TargetSpec(BaseModel):
    id: str = Field(min_length=1)
    strategy: Literal["test_id"] = "test_id"
    value: str = Field(min_length=1)
    robustness: str = Field(min_length=1)


class FillAction(BaseModel):
    id: str = Field(min_length=1)
    type: Literal["fill"] = "fill"
    target: TargetSpec
    value: str


class ClickAction(BaseModel):
    id: str = Field(min_length=1)
    type: Literal["click"] = "click"
    target: TargetSpec


class PressKeyAction(BaseModel):
    id: str = Field(min_length=1)
    type: Literal["press_key"] = "press_key"
    key: str = Field(min_length=1)
    target: TargetSpec | None = None


class WaitAction(BaseModel):
    id: str = Field(min_length=1)
    type: Literal["wait"] = "wait"
    target: TargetSpec
    condition: Literal["visible"] = "visible"
    timeout_ms: int = Field(gt=0)


class AssertAction(BaseModel):
    id: str = Field(min_length=1)
    type: Literal["assert"] = "assert"
    target: TargetSpec
    assertion: Literal["text_equals", "text_contains"] = "text_equals"
    expected: str


class ExtractAction(BaseModel):
    id: str = Field(min_length=1)
    type: Literal["extract"] = "extract"
    target: TargetSpec
    output: str = Field(min_length=1)
