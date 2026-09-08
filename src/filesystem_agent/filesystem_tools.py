import os
from collections.abc import Callable

from anthropic.types import ToolParam
from anthropic.types.tool_param import InputSchemaTyped

__all__ = ["dispatch", "tool_schemas"]


def cwd() -> str:
    return os.getcwd()


def list_dir(path: str) -> str:
    return "\n".join(os.listdir(path))


def dir_name(path: str) -> str:
    return os.path.basename(path)


def get_file_size(path: str) -> str:
    return str(os.path.getsize(path))


def get_file_content(path: str, n_characters: int = 25000) -> str:
    n_characters = min(n_characters, 25000)

    with open(path, "r") as file:
        content = file.read(n_characters)
        if len(content) >= 25000:
            return content + "...More content available in the file."
        return content


_TOOL_REGISTRY: dict[str, tuple[ToolParam, Callable]] = {
    "cwd": (
        ToolParam(
            name="cwd",
            description="Get the current working directory.",
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
                        "description": "Directory to list.",
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
                        "description": "Directory to get name of.",
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
                        "description": "File to get size of.",
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
                        "description": "File to get content of.",
                    },
                    "n_characters": {
                        "type": "integer",
                        "description": "Number of characters to read from the file. Defaults to 25000.",
                    }
                },
                required=["path"],
            ),
            input_examples=[
                {"path": "path/to/file.txt"},
                {"path": "path/to/file.txt", "n_characters": 10000},
            ]
        ),
        get_file_content,
    ),
}

tool_schemas: list[ToolParam] = [param for param, _func in _TOOL_REGISTRY.values()]


def dispatch(name: str, **kwargs) -> tuple[str, bool]:
    # TODO: Error handling
    is_error = False
    return _TOOL_REGISTRY[name][1](**kwargs), is_error
