"""Filesystem path validation shared by all entry points."""

from pathlib import Path


def validate_project_root(value: str) -> str:
    """Return the absolute path of an existing project directory.

    Surrounding whitespace is trimmed, `~` is expanded, and relative paths are
    resolved from the current working directory. Raise ValueError when the path is
    blank, missing, inaccessible, or not a directory.
    """
    if not value.strip():
        raise ValueError("Project root must be a non-empty directory path.")
    path = Path(value.strip()).expanduser()
    try:
        path = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError("Project root does not exist or cannot be accessed.") from error
    if not path.is_dir():
        raise ValueError("Project root must be a directory.")
    return str(path)
