"""Tools for searching Gerrit changes."""

import datetime
from typing import Any

from pydantic import BaseModel, Field

from ai_tools_gerrit.gerrit_client import GerritClient


def _sort_by_date(changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(changes, key=lambda c: c.get("updated", ""), reverse=True)


def _format_changes(changes: list[dict[str, Any]], query: str) -> str:
    if not changes:
        return f"No changes found for query: {query}"
    output = f'Found {len(changes)} changes for query "{query}":\n'
    for change in changes:
        wip = "[WIP] " if change.get("work_in_progress") else ""
        output += f"- {change['_number']}: {wip}{change['subject']}\n"
    if changes and changes[-1].get("_more_changes"):
        output += "\n(More changes available. Increase limit or refine query.)\n"
    return output


class QueryChangesInput(BaseModel):
    """Input for searching Gerrit changes by query string."""

    query: str = Field(
        description="Gerrit query string (e.g. 'status:open owner:me', 'is:reviewer').",
        examples=["status:open owner:me", "project:my-project is:reviewer"],
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of results to return.",
        examples=[25, 100],
    )
    options: list[str] | None = Field(
        default=None,
        description="Additional query options (e.g. ['CURRENT_REVISION', 'DETAILED_LABELS']).",
        examples=[["CURRENT_REVISION"], ["DETAILED_LABELS", "MESSAGES"]],
    )


def query_changes(
    query: str,
    gerrit: GerritClient,
    limit: int | None = None,
    options: list[str] | None = None,
) -> str:
    """Search for Gerrit changes matching a query.

    Searches the Gerrit instance for CLs matching the given query string.
    Results are sorted by most recently updated.

    Args:
        query: Gerrit query string (e.g. ``status:open owner:me``).
        gerrit: Gerrit client instance.
        limit: Maximum number of results to return.
        options: Additional Gerrit query options.

    Returns:
        Formatted string listing matching changes with CL numbers and subjects.
    """
    params: dict[str, Any] = {"q": query}
    if limit is not None:
        params["n"] = limit
    if options:
        params["o"] = options

    changes: list[dict[str, Any]] = gerrit.get("/changes/", params=params)
    changes = _sort_by_date(changes)
    return _format_changes(changes, query)


class QueryChangesByDateInput(BaseModel):
    """Input for searching Gerrit changes within a date range."""

    start_date: str = Field(
        description="Start date in YYYY-MM-DD format (inclusive).",
        examples=["2025-01-01"],
    )
    end_date: str = Field(
        description="End date in YYYY-MM-DD format (inclusive).",
        examples=["2025-01-31"],
    )
    status: str = Field(
        default="merged",
        description="Change status to filter by (e.g. 'merged', 'open', 'abandoned').",
        examples=["merged", "open"],
    )
    project: str | None = Field(
        default=None,
        description="Optional project name to filter results.",
        examples=["my-project"],
    )
    message_substring: str | None = Field(
        default=None,
        description="Optional substring to search for in commit messages.",
        examples=["fix: null pointer"],
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of results to return.",
        examples=[50],
    )


def query_changes_by_date(
    start_date: str,
    end_date: str,
    gerrit: GerritClient,
    status: str = "merged",
    project: str | None = None,
    message_substring: str | None = None,
    limit: int | None = None,
) -> str:
    """Search for Gerrit changes within a date range with optional filters.

    Constructs a Gerrit query for changes in the given date window, optionally
    filtered by project, commit message content, and status.

    Args:
        start_date: Start date in YYYY-MM-DD format (inclusive).
        end_date: End date in YYYY-MM-DD format (inclusive).
        gerrit: Gerrit client instance.
        status: Change status (default ``merged``).
        project: Optional project name filter.
        message_substring: Optional substring to search in commit messages.
        limit: Maximum number of results.

    Returns:
        Formatted string listing matching changes.
    """
    try:
        parsed_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        parsed_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD for start_date and end_date."

    # Gerrit's 'before' operator is exclusive, so add one day
    exclusive_end = (parsed_end + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    parts = [
        f"status:{status}",
        f"after:{parsed_start.strftime('%Y-%m-%d')}",
        f"before:{exclusive_end}",
    ]
    if project:
        parts.append(f"project:{project}")
    if message_substring:
        parts.append(f'message:"{message_substring}"')

    full_query = " ".join(parts)
    return query_changes(query=full_query, gerrit=gerrit, limit=limit)


class GetMostRecentClInput(BaseModel):
    """Input for retrieving the most recent CL authored by a user."""

    user: str = Field(
        description="Gerrit account identifier (email, username, or account ID).",
        examples=["jane.doe@example.com", "jdoe"],
    )


def get_most_recent_cl(user: str, gerrit: GerritClient) -> str:
    """Get the most recently updated change authored by a user.

    Args:
        user: Gerrit account identifier (email, username, or account ID).
        gerrit: Gerrit client instance.

    Returns:
        Formatted string with the most recent CL's number and subject,
        or a message if no changes are found.
    """
    params: dict[str, Any] = {"q": f"owner:{user}", "n": 1}
    changes: list[dict[str, Any]] = gerrit.get("/changes/", params=params)

    if not changes:
        return f"No changes found for user: {user}"

    change = changes[0]
    wip = "[WIP] " if change.get("work_in_progress") else ""
    return f"Most recent CL for {user}:\n- {change['_number']}: {wip}{change['subject']}\n"
