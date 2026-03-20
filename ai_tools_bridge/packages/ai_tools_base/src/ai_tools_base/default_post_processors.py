"""Default post processors for common output transformations.

This module provides reusable post processors that can be applied to tool outputs
for common formatting needs like JSON serialization and markdown formatting.
"""

import json
from typing import Any

from pydantic import BaseModel

from .model import PostProcessor


def convert_to_json(result: dict[str, Any] | list[Any] | BaseModel | str | int | float | bool | None) -> str:
    """Convert a tool result to a JSON string.

    Handles Pydantic models, dicts, lists, and primitive types.

    Args:
        result: The tool output to convert. Supports:
            - Pydantic BaseModel instances
            - Dictionaries
            - Lists (including lists of Pydantic models)
            - Primitive types (str, int, float, bool, None)

    Returns:
        A JSON string representation of the result.
    """
    if isinstance(result, BaseModel):
        return result.model_dump_json(indent=2)

    return json.dumps(result, indent=2, default=str)


def convert_to_markdown(
    result: dict[str, Any] | list[Any] | BaseModel | str | int | float | bool | None,
) -> str:
    """Convert a tool result to a markdown-formatted string.

    Creates a markdown representation of the result based on its type.

    Args:
        result: The tool output to convert. Supports:
            - Pydantic BaseModel instances (key-value format)
            - Dictionaries (key-value format)
            - Lists (bullet points)
            - Primitive types (str, int, float, bool, None) - direct string representation

    Returns:
        A markdown string representation of the result.
    """
    if result is None:
        return "None"

    if isinstance(result, bool):
        return str(result)

    if isinstance(result, str | int | float):
        return str(result)

    if isinstance(result, list):
        if not result:
            return ""
        lines: list[str] = []
        for item in result:  # pyright: ignore[reportUnknownVariableType]
            if isinstance(item, BaseModel):
                lines.append(f"- {json.dumps(item.model_dump())}")
            elif isinstance(item, dict):
                lines.append(f"- {json.dumps(item)}")
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)

    if isinstance(result, BaseModel):
        data = result.model_dump()
    else:
        data = result

    lines = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"**{key}:**")
            for item in value:  # pyright: ignore[reportUnknownVariableType]
                if isinstance(item, dict):
                    lines.append(f"  - {json.dumps(item)}")
                else:
                    lines.append(f"  - {item}")
        elif isinstance(value, dict):
            lines.append(f"**{key}:** {json.dumps(value)}")
        else:
            lines.append(f"**{key}:** {value}")

    return "\n".join(lines)


# Pre-configured PostProcessor instances for easy reuse
to_json = PostProcessor(
    name="json",
    func=convert_to_json,
)
"""Post processor that converts tool output to JSON string format."""

to_markdown = PostProcessor(
    name="markdown",
    func=convert_to_markdown,
)
"""Post processor that converts tool output to markdown format."""
