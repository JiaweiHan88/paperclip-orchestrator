"""Update JIRA ticket functionality."""

from typing import Any

from jira import JIRA, Issue
from pydantic import BaseModel, Field

from .fields import resolve_field_updates
from .markup_converter import markdown_to_jira


class UpdateJiraTicketInput(BaseModel):
    """Input model for updating an existing JIRA ticket.

    Args:
        issue_key: The JIRA issue key (e.g., 'PROJ-123').
        summary: Optional new title/summary of the ticket.
        description: Optional new detailed description of the ticket.
        definition_of_done: Optional list of checklist items for definition of done.
        acceptance_criteria: Optional list of checklist items for acceptance criteria.
        assignee: Optional assignee username.
        priority: Optional priority level.
        labels: Optional list of labels.
        components: Optional list of component names.
        custom_fields: Optional dictionary of custom fields by field name or ID.
    """

    issue_key: str = Field(
        description="The JIRA issue key (e.g., 'PROJ-123').",
        examples=["SWH-123", "MCP-456", "PROJ-789"],
    )
    summary: str | None = Field(
        default=None,
        description="Optional new title/summary of the ticket.",
        examples=["Implement user authentication", "Fix login bug"],
    )
    description: str | None = Field(
        default=None,
        description=(
            "Optional new detailed description of the ticket. "
            "Markdown formatting will be automatically converted to JIRA wiki markup. "
            "Supports headers (##), bold (**text**), bullets (-), numbered lists (1.), "
            "inline code (`code`), and code blocks (```)."
        ),
        examples=["This ticket implements user authentication using OAuth2..."],
    )
    definition_of_done: list[str] | None = Field(
        default=None,
        description="Optional list of checklist items for definition of done. If provided, replaces existing list.",
        examples=[["Unit tests written", "Code reviewed", "Documentation updated"]],
    )
    acceptance_criteria: list[str] | None = Field(
        default=None,
        description="Optional list of checklist items for acceptance criteria. If provided, replaces existing list.",
        examples=[["User can login successfully", "Invalid credentials show error"]],
    )
    assignee: str | None = Field(
        default=None,
        description="Optional assignee username.",
        examples=["john.doe", "jane.smith"],
    )
    priority: str | None = Field(
        default=None,
        description="Optional priority level.",
        examples=["High", "Medium", "Low", "Critical"],
    )
    labels: list[str] | None = Field(
        default=None,
        description="Optional list of labels to set.",
        examples=[["bug", "urgent"], ["feature", "enhancement"]],
    )
    components: list[str] | None = Field(
        default=None,
        description="Optional list of component names.",
        examples=[["Frontend"], ["Backend", "API"]],
    )
    custom_fields: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional dictionary of custom fields to update. Use field names or field IDs. "
            "Use get_jira_fields tool to discover available custom fields and their IDs."
        ),
        examples=[
            {"Epic Link": "PROJ-100"},
            {"customfield_10500": "Custom value"},
        ],
    )


def update_jira_ticket(
    issue_key: str,
    jira_instance: JIRA,
    summary: str | None = None,
    description: str | None = None,
    definition_of_done: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    labels: list[str] | None = None,
    components: list[str] | None = None,
    custom_fields: dict[str, Any] | None = None,
) -> str:
    """Update an existing JIRA ticket with new field values.

    This function uses field discovery to automatically:
        - Resolve field names to field IDs
        - Format values based on field types
        - Handle both system and custom fields

    Args:
        issue_key: The JIRA issue key (e.g., 'PROJ-123').
        jira_instance: JIRA instance to use for the operation.
        summary: Optional new title/summary of the ticket.
        description: Optional new detailed description of the ticket.
        definition_of_done: Optional list of checklist items for definition of done.
        acceptance_criteria: Optional list of checklist items for acceptance criteria.
        assignee: Optional assignee username.
        priority: Optional priority level.
        labels: Optional list of labels.
        components: Optional list of component names.
        custom_fields: Optional dictionary of custom fields by field name or ID.

    Returns:
        Markdown formatted string with ticket update result and details.

    Raises:
        jira.exceptions.JIRAError: If the issue does not exist, access is denied,
            or the update fails.

    Examples:
        Update standard fields:
        >>> update_jira_ticket("PROJ-123", jira, summary="New title", priority="High")

        Update with custom fields:
        >>> update_jira_ticket("PROJ-123", jira, custom_fields={"Epic Link": "PROJ-100"})

        Update definition of done:
        >>> update_jira_ticket("PROJ-123", jira, definition_of_done=["Tests", "Review"])
    """
    # Get the existing issue
    issue: Issue = jira_instance.issue(issue_key)  # pyright: ignore

    # Build fields dictionary from parameters
    fields: dict[str, Any] = {}

    if summary is not None:
        fields["summary"] = summary

    if description is not None:
        # Convert markdown to JIRA wiki markup
        fields["description"] = markdown_to_jira(description)

    if definition_of_done is not None:
        fields["definition of done"] = definition_of_done

    if acceptance_criteria is not None:
        fields["acceptance criteria"] = acceptance_criteria

    if assignee is not None:
        fields["assignee"] = assignee

    if priority is not None:
        fields["priority"] = priority

    if labels is not None:
        fields["labels"] = labels

    if components is not None:
        fields["components"] = components

    # Add custom fields if provided
    if custom_fields:
        fields.update(custom_fields)

    # Resolve field names to IDs and format values
    resolved_fields = resolve_field_updates(fields, jira_instance)

    # Update the issue if there are fields to update
    if resolved_fields:
        issue.update(fields=resolved_fields)  # pyright: ignore

        # Build result with updated fields
        result = f"# JIRA Ticket {issue_key} Updated Successfully\n\n"
        result += f"**Updated {len(resolved_fields)} field(s)**\n\n"

        # List updated fields
        for field_id in resolved_fields:
            result += f"- {field_id}\n"

        return result
    else:
        return f"No fields to update for JIRA Ticket {issue_key}"
