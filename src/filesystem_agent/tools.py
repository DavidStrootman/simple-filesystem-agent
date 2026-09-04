import os
from typing import Callable

from anthropic.types import ToolParam
from anthropic.types.tool_param import InputSchemaTyped

__all__ = ["tool_schemas"]


def list_dir(path: str) -> list[str]:
    return os.listdir(path)


def cwd() -> str:
    return os.getcwd()


_TOOL_REGISTRY: dict[str, tuple[ToolParam, Callable]] = {
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
}

tool_schemas = [schema for _name, schema in _TOOL_REGISTRY.items()]
