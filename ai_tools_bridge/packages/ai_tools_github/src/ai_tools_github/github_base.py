"""Base model for GitHub GraphQL response objects, replacing gitaudit.github.graphql_base.GraphQlBase."""

from typing import Any, cast

from pydantic import BaseModel, ConfigDict, model_validator


def _to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case, handling acronyms like HTML, URL, etc."""
    result: list[str] = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            # Don't add underscore if previous char is also uppercase and next is uppercase or end
            prev_upper = name[i - 1].isupper()
            next_upper = (i + 1 < len(name) and name[i + 1].isupper()) or i + 1 == len(name)
            if not (prev_upper and next_upper):
                result.append("_")
        result.append(char.lower())
    return "".join(result)


class GraphQlModel(BaseModel):
    """Base model for GitHub GraphQL response objects.

    Provides:
    - camelCase to snake_case alias generation
    - Automatic unwrapping of {nodes: [...]} patterns in GraphQL responses
    """

    model_config = ConfigDict(
        alias_generator=_to_snake_case,
        populate_by_name=True,
    )

    typename: str | None = None

    @model_validator(mode="before")
    @classmethod
    def unwrap_nodes(cls, data: Any) -> Any:
        """Convert camelCase keys to snake_case and unwrap {nodes: [...]} patterns."""
        if not isinstance(data, dict):
            return data
        result: dict[str, Any] = {}
        for key, value in cast(dict[str, Any], data).items():
            snake_key = _to_snake_case(key)
            if isinstance(value, dict) and "nodes" in value:
                result[snake_key] = value["nodes"]
            else:
                result[snake_key] = value
        return result
