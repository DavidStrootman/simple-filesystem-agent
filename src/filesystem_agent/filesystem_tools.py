import os
from collections.abc import Callable
from pathlib import Path

from anthropic.types import ToolParam
from anthropic.types.tool_param import InputSchemaTyped

import config

__all__ = ["dispatch", "tool_schemas"]


def to_real_path(path: str) -> Path:
    """Translate a model-facing path (always relative to the sandbox root,
    "." meaning the root itself) into a validated, real filesystem path.

    Resolves first so `..` segments and symlinks are collapsed before the
    containment check runs — checking an unresolved path would let either
    of those escape the sandbox undetected.
    """
    home = config.sandbox_home.resolve()
    real = (home / path.lstrip("/")).resolve()
    if not real.is_relative_to(home):
        raise ValueError(f"Path '{path}' is outside the allowed directory.")
    return real


def to_virtual_path(real_path: Path) -> str:
    """Real filesystem path -> the sandbox-root-relative form shown to the
    model. The inverse of to_real_path; used for anything a tool returns
    that would otherwise leak a real, absolute host path."""
    home = config.sandbox_home.resolve()
    relative = real_path.resolve().relative_to(home)
    return str(relative)


def cwd() -> str:
    real_cwd = Path.cwd().resolve()
    try:
        return to_virtual_path(real_cwd)
    except ValueError:
        # Process cwd happens to be outside the sandbox root — report the
        # root itself rather than leaking the real path.
        return "."


def list_dir(path: str) -> str:
    return "\n".join(os.listdir(to_real_path(path)))


def dir_name(path: str) -> str:
    # Routed through to_real_path purely for validation consistency: every
    # path-taking tool must enforce the same sandbox containment rule on
    # `path`, even though this one doesn't otherwise need disk access.
    return to_real_path(path).name


def get_file_size(path: str) -> str:
    return str(os.path.getsize(to_real_path(path)))


def get_file_content(path: str, n_characters: int = 25000) -> str:
    n_characters = min(n_characters, 25000)

    with open(to_real_path(path), "r") as file:
        content = file.read(n_characters)
        if len(content) >= 25000:
            return content + "...More content available in the file."
        return content


_MAX_SEARCH_RESULTS = 200


def search_files(path: str, pattern: str = "*") -> str:
    real = to_real_path(path)
    matches = sorted(real.rglob(pattern))
    truncated = len(matches) > _MAX_SEARCH_RESULTS
    matches = matches[:_MAX_SEARCH_RESULTS]

    lines = [
        to_virtual_path(match) + ("/" if match.is_dir() else "") for match in matches
    ]
    result = "\n".join(lines)
    if truncated:
        result += (
            f"\n...{_MAX_SEARCH_RESULTS} results shown, more are available. "
            "Narrow the pattern or path to see the rest."
        )
    return result


_PATH_DESCRIPTION_SUFFIX = (
    " Relative to the sandbox root — use '.' for the root itself. "
    "There is no path outside this root; do not use absolute paths."
)

_TOOL_REGISTRY: dict[str, tuple[ToolParam, Callable]] = {
    "cwd": (
        ToolParam(
            name="cwd",
            description="Get the current working directory, relative to the sandbox root.",
            input_schema=InputSchemaTyped(
                type="object",
                properties={},
                required=[],
            ),
        ),
        cwd,
    ),
    "list_dir": (
        ToolParam(
            name="list_dir",
            description="List the contents of a directory.",
            input_schema=InputSchemaTyped(
                type="object",
                properties={
                    "path": {
                        "type": "string",
                        "description": "Directory to list." + _PATH_DESCRIPTION_SUFFIX,
                    },
                },
                required=["path"],
            ),
        ),
        list_dir,
    ),
    "dir_name": (
        ToolParam(
            name="dir_name",
            description="Get the name of the directory.",
            input_schema=InputSchemaTyped(
                type="object",
                properties={
                    "path": {
                        "type": "string",
                        "description": "Directory to get name of."
                        + _PATH_DESCRIPTION_SUFFIX,
                    },
                },
                required=["path"],
            ),
        ),
        dir_name,
    ),
    "get_file_size": (
        ToolParam(
            name="get_file_size",
            description="Get the size of a file in bytes.",
            input_schema=InputSchemaTyped(
                type="object",
                properties={
                    "path": {
                        "type": "string",
                        "description": "File to get size of." + _PATH_DESCRIPTION_SUFFIX,
                    },
                },
                required=["path"],
            ),
        ),
        get_file_size,
    ),
    "get_file_content": (
        ToolParam(
            name="get_file_content",
            description="Get the content of a file. Reads at most 25000 characters. You must inform the user if the file is too large.",
            input_schema=InputSchemaTyped(
                type="object",
                properties={
                    "path": {
                        "type": "string",
                        "description": "File to get content of."
                        + _PATH_DESCRIPTION_SUFFIX,
                    },
                    "n_characters": {
                        "type": "integer",
                        "description": "Number of characters to read from the file. Defaults to 25000.",
                    },
                },
                required=["path"],
            ),
            input_examples=[
                {"path": "path/to/file.txt"},
                {"path": "path/to/file.txt", "n_characters": 10000},
            ],
        ),
        get_file_content,
    ),
    "search_files": (
        ToolParam(
            name="search_files",
            description=(
                "Recursively search a directory for files and subdirectories "
                "matching a glob pattern, at any depth. Use this instead of "
                "repeatedly calling list_dir on nested folders one at a time — "
                "one call here covers the whole subtree."
            ),
            input_schema=InputSchemaTyped(
                type="object",
                properties={
                    "path": {
                        "type": "string",
                        "description": "Directory to search, recursively."
                        + _PATH_DESCRIPTION_SUFFIX,
                    },
                    "pattern": {
                        "type": "string",
                        "description": (
                            "Glob pattern to match, e.g. '*' for everything, "
                            "'*.py' for Python files at any depth, "
                            "'config*' for names starting with 'config'. "
                            "Defaults to '*' (match everything)."
                        ),
                    },
                },
                required=["path"],
            ),
            input_examples=[
                {"path": "."},
                {"path": "repos/simple-filesystem-agent", "pattern": "*.py"},
            ],
        ),
        search_files,
    ),
}

tool_schemas: list[ToolParam] = [param for param, _func in _TOOL_REGISTRY.values()]


def dispatch(name: str, **kwargs) -> tuple[str, bool]:
    tool = _TOOL_REGISTRY.get(name)
    if tool is None:
        return f"Unknown tool: '{name}'.", True

    _schema, func = tool
    try:
        return func(**kwargs), False
    except ValueError as e:
        # Sandbox rejection from to_real_path, or any other bad-input case
        # a tool raises ValueError for.
        return str(e), True
    except TypeError as e:
        # Wrong/missing arguments for this tool's signature.
        return f"Invalid arguments for tool '{name}': {e}", True
    except OSError as e:
        # FileNotFoundError, PermissionError, IsADirectoryError, etc. from
        # the actual filesystem call.
        return f"Error accessing path for tool '{name}': {e}", True
    except Exception as e:
        # Catch-all so a tool bug still surfaces as a tool_result instead
        # of crashing the whole loop.
        return f"Unexpected error running tool '{name}': {e}", True
