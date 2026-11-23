"""Docker context and container elicitation models and resolvers."""

from pathlib import Path
from typing import Annotated

from mcp.server.mcpserver import Elicit, Resolve
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator

from core.docker import list_docker_contexts, list_running_containers

from ._common import _remove_elicitation_metadata
from .project_root import ProjectRootInput


class DockerChoiceInput(BaseModel):
    """A Docker context or container selected from discovered options."""

    model_config = ConfigDict(json_schema_extra=_remove_elicitation_metadata)

    choice: str = Field(min_length=1, description="Select a Docker target.")


def _docker_choice(message: str, options: list[str]) -> Elicit[DockerChoiceInput]:
    """Limit an elicitation response to the discovered Docker options."""
    def validate_choice(value: str) -> str:
        if value not in options:
            raise ValueError("Choose one of the discovered Docker options.")
        return value

    choice_model = create_model(
        "DockerTargetChoice",
        __base__=DockerChoiceInput,
        __validators__={"validate_choice": field_validator("choice")(validate_choice)},
        choice=(
            str,
            Field(
                description="Select a Docker target.",
                json_schema_extra={"enum": options},
            ),
        ),
    )
    return Elicit(message, choice_model)


def request_docker_context(project_root: str) -> Elicit[DockerChoiceInput]:
    """Create the output folder and ask where the target container exists."""
    try:
        root = ProjectRootInput(project_root=project_root).project_root
        (Path(root) / ".polymock" / "populate").mkdir(parents=True, exist_ok=True)
        contexts = list_docker_contexts()
    except (OSError, ValueError) as error:
        raise ToolError(str(error)) from error
    if not contexts:
        raise ToolError("No Docker contexts are configured on this machine.")
    return _docker_choice(
        "Which Docker environment (context) contains the target container?", contexts,
    )


def request_docker_container(
    docker_context: Annotated[DockerChoiceInput, Resolve(request_docker_context)],
) -> Elicit[DockerChoiceInput]:
    """List running containers only in the environment selected by the user."""
    try:
        containers = list_running_containers(docker_context.choice)
    except (OSError, ValueError) as error:
        raise ToolError(str(error)) from error
    if not containers:
        raise ToolError(f"No running containers found in Docker context {docker_context.choice!r}.")
    details = "\n".join(
        f"{item['Names']} ({item['Image']})" for item in containers
    )
    return _docker_choice(
        f"Choose the target container in Docker context {docker_context.choice!r}.\n"
        f"Running containers (name, image):\n{details}",
        [item["Names"] for item in containers],
    )
