"""Local models for GitHub issues, replacing gitaudit.github.graphql_objects models.

These are minimal models matching the GraphQL response shapes used in issues.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case, handling acronyms like HTML, URL, etc."""
    result: list[str] = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            prev_upper = name[i - 1].isupper()
            next_upper = (i + 1 < len(name) and name[i + 1].isupper()) or i + 1 == len(name)
            if not (prev_upper and next_upper):
                result.append("_")
        result.append(char.lower())
    return "".join(result)


class _IssueBase(BaseModel):
    """Base model with camelCase alias support and nodes unwrapping."""

    model_config = ConfigDict(
        alias_generator=_to_snake_case,
        populate_by_name=True,
    )

    typename: str | None = Field(default=None, alias="__typename")

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


class IssueAuthor(_IssueBase):
    """Author of a comment or issue."""

    login: str | None = None


class IssueComment(_IssueBase):
    """Comment on an issue."""

    author: IssueAuthor | None = None
    body: str | None = None
    body_html: str | None = None
    created_at: datetime | None = None


class IssuePullRequest(_IssueBase):
    """Pull request referenced from an issue (lightweight model)."""

    number: int | None = None
    title: str | None = None
    url: str | None = None
    merged: bool | None = None


class IssueLabel(_IssueBase):
    """Issue label."""

    name: str


class ReferencedCommit(_IssueBase):
    """Referenced commit in timeline."""

    oid: str | None = None
    message: str | None = None
    committed_date: datetime | None = None


class ReferencedEvent(_IssueBase):
    """Referenced event in timeline."""

    created_at: datetime | None = None
    commit: ReferencedCommit | None = None


class CrossReferencedSource(_IssueBase):
    """Source of a cross-referenced event (can be a PR or Issue)."""

    number: int | None = None
    title: str | None = None
    url: str | None = None
    merged: bool | None = None
    body: str | None = None
    labels: list[IssueLabel] | None = None


class CrossReferencedEvent(_IssueBase):
    """Cross-referenced event in timeline."""

    created_at: datetime | None = None
    source: CrossReferencedSource | None = None


class Issue(_IssueBase):
    """GitHub issue with fields matching the QUERY_ISSUE_DATA GraphQL query."""

    title: str | None = None
    number: int | None = None
    url: str | None = None
    body: str | None = None
    body_html: str | None = None
    labels: list[IssueLabel] | None = Field(default=None)
    comments: list[IssueComment] | None = Field(default=None)
    timeline_items: list[CrossReferencedEvent | ReferencedEvent] | None = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def parse_timeline_items(cls, data: Any) -> Any:
        """Parse timeline items by discriminating on __typename.

        Note: The parent _IssueBase.unwrap_nodes validator converts camelCase keys
        to snake_case and unwraps {nodes: [...]} before this runs.
        """
        if not isinstance(data, dict):
            return data
        data = dict(cast(dict[str, Any], data))

        # Parse timeline_items based on __typename
        raw_items = data.get("timeline_items")
        if isinstance(raw_items, list):
            parsed: list[CrossReferencedEvent | ReferencedEvent] = []
            for item in cast(list[Any], raw_items):
                if not isinstance(item, dict):
                    continue
                typename = cast(dict[str, Any], item).get("__typename", "")
                if typename == "CrossReferencedEvent":
                    parsed.append(CrossReferencedEvent.model_validate(item))
                elif typename == "ReferencedEvent":
                    parsed.append(ReferencedEvent.model_validate(item))
            data["timeline_items"] = parsed

        return data
