"""Tools for managing reviewers on Gerrit changes."""

from typing import Any

from pydantic import BaseModel, Field

from ai_tools_gerrit.gerrit_client import GerritClient


class AddReviewerInput(BaseModel):
    """Input for adding a reviewer or CC to a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )
    reviewer: str = Field(
        description="Account email, username, or group name to add.",
        examples=["jane.doe@example.com", "my-team-group"],
    )
    state: str = Field(
        default="REVIEWER",
        description="Role to assign: 'REVIEWER' (can vote) or 'CC' (notify only).",
        examples=["REVIEWER", "CC"],
    )


def add_reviewer(
    change_id: str,
    reviewer: str,
    gerrit: GerritClient,
    state: str = "REVIEWER",
) -> str:
    """Add a user or group as a reviewer or CC on a Gerrit change.

    Args:
        change_id: Change identifier.
        reviewer: Account email, username, or group name.
        gerrit: Gerrit client instance.
        state: ``'REVIEWER'`` to allow voting, ``'CC'`` for notification only.

    Returns:
        Confirmation message on success.

    Raises:
        ValueError: If an invalid state is provided.
    """
    if state.upper() not in ("REVIEWER", "CC"):
        raise ValueError(f"Invalid state '{state}'. Must be 'REVIEWER' or 'CC'.")

    payload = {"reviewer": reviewer, "state": state.upper()}
    gerrit.post(f"/changes/{change_id}/reviewers", payload=payload)
    return f"Successfully added '{reviewer}' as {state.upper()} on CL {change_id}."


class SuggestReviewersInput(BaseModel):
    """Input for suggesting reviewers for a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )
    query: str = Field(
        description="Partial name or email to search for.",
        examples=["jane", "doe@example"],
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of suggestions to return.",
        examples=[10],
    )
    exclude_groups: bool = Field(
        default=False,
        description="If True, only individual accounts are suggested (no groups).",
    )
    reviewer_state: str | None = Field(
        default=None,
        description="Filter by desired state: 'REVIEWER' or 'CC'.",
        examples=["REVIEWER", "CC"],
    )


def suggest_reviewers(
    change_id: str,
    query: str,
    gerrit: GerritClient,
    limit: int | None = None,
    exclude_groups: bool = False,
    reviewer_state: str | None = None,
) -> str:
    """Suggest reviewers for a Gerrit change based on a search query.

    Args:
        change_id: Change identifier.
        query: Partial name or email prefix to search for.
        gerrit: Gerrit client instance.
        limit: Maximum number of suggestions.
        exclude_groups: Exclude groups from results.
        reviewer_state: Optional desired reviewer state filter.

    Returns:
        Formatted list of suggested accounts and groups.
    """
    params: dict[str, Any] = {"q": query}
    if limit is not None:
        params["n"] = limit
    if exclude_groups:
        params["exclude-groups"] = ""
    if reviewer_state:
        params["reviewer-state"] = reviewer_state

    suggestions: list[dict[str, Any]] = gerrit.get(f"/changes/{change_id}/suggest_reviewers", params=params)

    if not suggestions:
        return "No reviewers found for the given query."

    output = "Suggested reviewers:\n"
    for suggestion in suggestions:
        if "account" in suggestion:
            acct = suggestion["account"]
            output += f"- {acct.get('name', '')} ({acct.get('email', 'no email')})\n"
        elif "group" in suggestion:
            grp = suggestion["group"]
            output += f"- Group: {grp.get('name', 'Unnamed Group')}\n"

    return output
