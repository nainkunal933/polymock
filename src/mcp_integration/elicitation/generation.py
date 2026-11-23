"""Generation target, staging, and record count elicitation models and resolvers."""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, Mapping

from mcp.server.mcpserver import Elicit, Resolve
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator

from core import (
    SandboxContext,
    build_context,
    copy_procedure_files,
    normalize_target_options,
)

from ._common import _remove_elicitation_metadata
from .project_root import ProjectRootInput


class GenerationTargetInput(BaseModel):
    """The table or collection selected from the host agent's options."""

    model_config = ConfigDict(
        json_schema_extra=_remove_elicitation_metadata,
        str_strip_whitespace=True,
    )

    target: str = Field(
        min_length=1,
        description="Choose the table or collection to target.",
    )


def request_generation_target(
    project_root: str,
    target_options: list[str],
) -> Elicit[GenerationTargetInput]:
    """Validate the supplied inputs and ask the user to select a target."""
    try:
        resolved_root = ProjectRootInput(project_root=project_root)
        options = normalize_target_options(target_options)
    except ValueError as error:
        raise ToolError(str(error)) from error

    def validate_target(value: str) -> str:
        if value not in options:
            raise ValueError("Choose one of the supplied target options.")
        return value

    choice_model = create_model(
        "GenerationTargetChoice",
        __base__=GenerationTargetInput,
        __validators__={"validate_target": field_validator("target")(validate_target)},
        target=(
            str,
            Field(
                description="Choose the table or collection to target.",
                json_schema_extra={"enum": options},
            ),
        ),
    )
    return Elicit(
        "Choose the table or collection to target in the project at: "
        f"{resolved_root.project_root}",
        choice_model,
    )


@dataclass(frozen=True, slots=True)
class PreparedGeneration:
    """Validated context and staged procedures for the selected target."""

    project_root: str
    target: str
    context: SandboxContext
    copied_files: tuple[str, ...]


def prepare_generation(
    objective: str,
    project_root: str,
    target_procedures: dict[str, list[str]],
    selection: Annotated[GenerationTargetInput, Resolve(request_generation_target)],
    values: dict[str, str] | None = None,
) -> PreparedGeneration:
    """Stage the selected target's procedures before asking for a record count.

    Resolvers can run again when MCP requests resume. The copier reuses identical
    files, so preparing the same generation again preserves staged files.
    """
    try:
        context = build_context(objective, values)
        resolved_root = ProjectRootInput(project_root=project_root)
        if selection.target not in target_procedures:
            raise ValueError(
                f"No procedure file mapping supplied for target: {selection.target}"
            )
        copied_files = copy_procedure_files(
            Path(resolved_root.project_root), target_procedures[selection.target]
        )
    except (OSError, ValueError) as error:
        raise ToolError(str(error)) from error
    return PreparedGeneration(
        project_root=resolved_root.project_root,
        target=selection.target,
        context=context,
        copied_files=tuple(str(path) for path in copied_files),
    )


class RecordCountChoice(BaseModel):
    """A preset record count or a request to enter a custom count."""

    model_config = ConfigDict(json_schema_extra=_remove_elicitation_metadata)

    choice: Literal["10", "50", "100", "Custom"] = Field(
        description="Choose how many records to create, or enter a custom count.",
    )


class RecordCountInput(BaseModel):
    """The positive whole-number count requested by the user."""

    model_config = ConfigDict(json_schema_extra=_remove_elicitation_metadata)

    record_count: int = Field(
        ge=1,
        strict=True,
        description="Number of records to create; enter a positive whole number.",
    )


RECORD_COUNT_VALUE_KEY = "record_count"


def supplied_record_count(values: Mapping[str, str] | None) -> int | None:
    """Return a context-supplied record count, or None when it was not supplied.

    Keys and values are trimmed like other context values; blank values count as
    not supplied. A supplied value must be a positive whole number.
    """
    raw = next(
        (
            value.strip()
            for key, value in (values or {}).items()
            if key.strip() == RECORD_COUNT_VALUE_KEY and value.strip()
        ),
        None,
    )
    if raw is None:
        return None
    if not (raw.isascii() and raw.isdigit()) or int(raw) < 1:
        raise ToolError(
            f"values[{RECORD_COUNT_VALUE_KEY!r}] must be a positive whole number; got {raw!r}."
        )
    return int(raw)


def request_record_count_choice(
    prepared: Annotated[PreparedGeneration, Resolve(prepare_generation)],
    values: dict[str, str] | None = None,
) -> RecordCountChoice | None | Elicit[RecordCountChoice]:
    """Offer record-count choices after staging, unless context supplies a count."""
    if supplied_record_count(values) is not None:
        return None
    return Elicit(
        f"How many records would you like to create for {prepared.target}? "
        "Choose 10, 50, 100, or Custom to enter another positive whole number.",
        RecordCountChoice,
    )


def resolve_record_count(
    choice: Annotated[RecordCountChoice | None, Resolve(request_record_count_choice)],
    values: dict[str, str] | None = None,
) -> RecordCountInput | Elicit[RecordCountInput]:
    """Honor a context-supplied count, resolve a preset, or ask for a custom count."""
    count = supplied_record_count(values)
    if count is not None:
        return RecordCountInput(record_count=count)
    if choice is None or choice.choice == "Custom":
        return Elicit(
            "How many records would you like to create? Enter a positive whole number.",
            RecordCountInput,
        )
    return RecordCountInput(record_count=int(choice.choice))
