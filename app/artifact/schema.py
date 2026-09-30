from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.artifact.actions import (
    AssertAction,
    ClickAction,
    ExtractAction,
    FillAction,
    PressKeyAction,
    WaitAction,
)


ValueType = Literal["string", "integer", "boolean", "money"]


class InputSpec(BaseModel):
    type: ValueType
    required: bool = True
    description: str = ""


class OutputSpec(BaseModel):
    type: ValueType
    description: str = ""


class SurfaceSpec(BaseModel):
    type: Literal["web"] = "web"
    application: str = Field(min_length=1)
    version: str = Field(min_length=1)


Action = Annotated[
    FillAction
    | ClickAction
    | PressKeyAction
    | WaitAction
    | AssertAction
    | ExtractAction,
    Field(discriminator="type"),
]


class SuccessSpec(BaseModel):
    checkpoint: str = Field(min_length=1, description="ID of the action whose successful completion establishes the recipe checkpoint.")


class Recipe(BaseModel):
    schema_version: str = "1.0"
    artifact_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = "1.0"
    goal: str = Field(min_length=1)

    surface: SurfaceSpec

    inputs: dict[str, InputSpec]
    actions: list[Action] = Field(min_length=1)

    outputs: dict[str, OutputSpec]

    success: SuccessSpec
