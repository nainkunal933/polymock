"""Project root elicitation models and resolvers."""

from pathlib import Path
from typing import Annotated, Literal

from mcp.server.mcpserver import Elicit, Resolve
from pydantic import BaseModel, ConfigDict, Field, field_validator

from core import validate_project_root

from ._common import _remove_elicitation_metadata


class ProjectRootChoice(BaseModel):
    """Whether to use the current folder or choose another directory."""

    model_config = ConfigDict(json_schema_extra=_remove_elicitation_metadata)

    choice: Literal["Use current folder", "Use another folder"] = Field(
        description="Choose the project folder to use."
    )


class ProjectRootInput(BaseModel):
    """Validated project root chosen by the user through elicitation."""

    model_config = ConfigDict(json_schema_extra=_remove_elicitation_metadata)

    project_root: str = Field(
        description=(
            "Relative or absolute path to an existing project directory on the "
            "machine running Polymock. Relative paths start from the current folder."
        )
    )

    @field_validator("project_root")
    @classmethod
    def validate_project_root(cls, value: str) -> str:
        return validate_project_root(value)


def _choose_project_root() -> Elicit[ProjectRootChoice]:
    """Offer the current folder first, with an option to override it."""
    return Elicit(
        f"Use the project in the current folder: {Path.cwd()}\n"
        "Use this folder or choose another folder with a relative or absolute path.",
        ProjectRootChoice,
    )


def resolve_project_root(
    selection: Annotated[ProjectRootChoice, Resolve(_choose_project_root)],
) -> ProjectRootInput | Elicit[ProjectRootInput]:
    """Resolve the selected folder, requesting an override only when needed."""
    if selection.choice == "Use current folder":
        return ProjectRootInput(project_root=str(Path.cwd()))
    return Elicit(
        "Enter the project's relative or absolute directory path. "
        f"Relative paths start from: {Path.cwd()}",
        ProjectRootInput,
    )
