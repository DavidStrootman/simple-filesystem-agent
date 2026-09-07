import os
from collections.abc import Callable

from anthropic.types import ToolParam
from anthropic.types.tool_param import InputSchemaTyped

__all__ = ["tool_schemas"]


def list_dir(path: str) -> str:
    return "\n".join(os.listdir(path))


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

tool_schemas: list[ToolParam] = [param for param, _func in _TOOL_REGISTRY.values()]


def dispatch(name: str, **kwargs) -> tuple[str, bool]:
    # TODO: Error handling
    is_error = False
    return _TOOL_REGISTRY[name][1](**kwargs), is_error