"""Jira issue transitions functionality."""

from typing import Any

from jira import JIRA
from pydantic import BaseModel, Field


class GetJiraTransitionsInput(BaseModel):
    """Input model for getting available transitions for a Jira issue.

    Args:
        issue_key: The key of the Jira issue (e.g., 'PROJECT-123').
    """

    issue_key: str = Field(
        description="The key of the Jira issue (e.g., 'PROJECT-123').",
        examples=["SWH-456", "MCP-789", "PROJ-123"],
    )


class TransitionJiraIssueInput(BaseModel):
    """Input model for transitioning a Jira issue to a new status.

    Args:
        issue_key: The key of the Jira issue (e.g., 'PROJECT-123').
        transition_id: The ID of the transition to perform.
        fields: Optional fields to update during the transition.
    """

    issue_key: str = Field(
        description="The key of the Jira issue (e.g., 'PROJECT-123').",
        examples=["SWH-456", "MCP-789", "PROJ-123"],
    )
    transition_id: str = Field(
        description="The ID of the transition to perform. Use get_jira_transitions to find available transition IDs.",
        examples=["11", "21", "31", "41"],
    )
    fields: dict[str, Any] | None = Field(
        default=None,
        description="Optional fields to update during the transition (e.g., resolution, assignee).",
        examples=[{"resolution": {"name": "Fixed"}}, {"assignee": {"name": "john.doe"}}],
    )


def get_jira_transitions(
    issue_key: str,
    jira_instance: JIRA,
) -> str:
    """Get the available status transitions for a JIRA issue.

    Returns a list of valid transitions that can be performed on the issue
    based on its current status and the workflow configuration.

    Args:
        issue_key: The key of the JIRA issue (e.g., 'PROJECT-123').
        jira_instance: JIRA instance to use for the operation.

    Returns:
        Markdown formatted string listing available transitions with their
        IDs and target statuses.

    Raises:
        jira.exceptions.JIRAError: If the issue does not exist or access is denied.
    """
    transitions = jira_instance.transitions(issue_key)  # pyright: ignore

    if not transitions:
        return f"No transitions available for issue {issue_key}"

    # Format transitions as markdown
    result = f"# Available Transitions for {issue_key}\n\n"
    for transition in transitions:
        transition_id = transition.get("id", "")
        transition_name = transition.get("name", "")

        # Get the target status if available
        to_status = ""
        if "to" in transition and isinstance(transition["to"], dict):
            to_status = f" → {transition['to'].get('name', '')}"

        result += f"- **{transition_name}** (ID: `{transition_id}`){to_status}\n"

    return result


def transition_jira_issue(
    issue_key: str,
    transition_id: str,
    jira_instance: JIRA,
    fields: dict[str, Any] | None = None,
) -> str:
    """Transition a JIRA issue to a new status.

    Performs a workflow transition on the specified issue. Use
    get_jira_transitions to discover available transition IDs.

    Args:
        issue_key: The key of the JIRA issue (e.g., 'PROJECT-123').
        transition_id: The ID of the transition to perform.
        jira_instance: JIRA instance to use for the operation.
        fields: Optional fields to update during the transition
            (e.g., resolution, assignee).

    Returns:
        Markdown formatted string with transition result and new status.

    Raises:
        jira.exceptions.JIRAError: If the transition fails (e.g., invalid
            transition ID, missing required fields, or permission denied).
    """
    # Prepare the transition data
    transition_data: dict[str, Any] = {}

    # Add fields if provided
    if fields:
        transition_data["fields"] = fields

    # Perform the transition
    jira_instance.transition_issue(issue_key, transition_id, **transition_data)  # pyright: ignore

    # Get the updated issue to confirm the transition
    issue = jira_instance.issue(issue_key)
    current_status = issue.fields.status.name  # pyright: ignore

    result = "# Transition Successful\n\n"
    result += f"Issue **{issue_key}** has been transitioned.\n\n"
    result += f"**Current Status:** {current_status}\n"

    return result
