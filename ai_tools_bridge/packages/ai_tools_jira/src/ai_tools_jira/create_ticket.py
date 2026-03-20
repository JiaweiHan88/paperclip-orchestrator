"""Create JIRA ticket functionality."""

from typing import Any

from jira import JIRA, Issue
from pydantic import BaseModel, Field

from .fields import resolve_field_updates
from .markup_converter import markdown_to_jira


class CreateJiraTicketInput(BaseModel):
    """Input model for creating a new JIRA ticket.

    Args:
        project_key: The JIRA project key (e.g., 'PROJ').
        issue_type: The type of issue (e.g., 'Story', 'Task', 'Bug').
        summary: The title/summary of the ticket.
        description: The detailed description of the ticket.
        definition_of_done: List of checklist items for definition of done.
        acceptance_criteria: List of checklist items for acceptance criteria.
        assignee: Optional assignee username.
        priority: Optional priority level.
    """

    project_key: str = Field(
        description="The JIRA project key (e.g., 'PROJ').",
        examples=["SWH", "MCP", "PROJ"],
    )
    issue_type: str = Field(
        description="The type of issue (e.g., 'Story', 'Task', 'Bug').",
        examples=["Story", "Task", "Bug", "Epic"],
    )
    summary: str = Field(
        description="The title/summary of the ticket.",
        examples=["Implement user authentication", "Fix login bug"],
    )
    description: str = Field(
        description=(
            "The detailed description of the ticket. "
            "Markdown formatting will be automatically converted to JIRA wiki markup. "
            "Supports headers (##), bold (**text**), bullets (-), numbered lists (1.), "
            "inline code (`code`), and code blocks (```)."
        ),
        examples=["This ticket implements user authentication using OAuth2..."],
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
    components: list[str] | None = Field(
        default=None,
        description="Optional list of component names.",
        examples=[["Frontend"], ["Backend", "API"]],
    )
    custom_fields: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional dictionary of custom fields to set. Use field names or field IDs. "
            "Use get_jira_fields tool to discover available custom fields and their IDs."
        ),
        examples=[
            {"Epic Name": "My Epic"},
            {"Epic Link": "PROJ-100"},
            {"Parent Link": "PROJ-200"},
        ],
    )


def create_jira_ticket(
    project_key: str,
    issue_type: str,
    summary: str,
    description: str,
    jira_instance: JIRA,
    assignee: str | None = None,
    priority: str | None = None,
    components: list[str] | None = None,
    custom_fields: dict[str, Any] | None = None,
) -> str:
    """Create a new JIRA ticket with the specified details.

    Creates a new issue in JIRA with support for standard fields (summary,
    description, assignee, priority, components) and custom checklist fields
    for definition of done and acceptance criteria.

    Args:
        project_key: The JIRA project key (e.g., 'PROJ').
        issue_type: The type of issue (e.g., 'Story', 'Task', 'Bug').
        summary: The title/summary of the ticket.
        description: The detailed description of the ticket.
        definition_of_done: Optional list of checklist items for definition of done.
        acceptance_criteria: Optional list of checklist items for acceptance criteria.
        assignee: Optional assignee username.
        priority: Optional priority level (e.g., 'High', 'Medium', 'Low').
        components: Optional list of component names.
        custom_fields: Optional dictionary of custom fields by field name or ID.

    Returns:
        Success message containing the created ticket key.

    Raises:
        jira.exceptions.JIRAError: If ticket creation fails (e.g., invalid project,
            missing required fields, or permission denied).
    """
    # Handle optional parameters

    # Convert markdown to JIRA wiki markup
    jira_description = markdown_to_jira(description)

    # Prepare the issue fields
    issue_dict: dict[str, Any] = {
        "project": {"key": project_key},
        "summary": summary,
        "description": jira_description,
        "issuetype": {"name": issue_type},
    }

    # Add optional fields if provided
    if assignee:
        issue_dict["assignee"] = {"name": assignee}

    if priority:
        issue_dict["priority"] = {"name": priority}

    if components:
        issue_dict["components"] = [{"name": comp} for comp in components]

    # Resolve and add custom fields if provided
    if custom_fields:
        resolved_custom_fields = resolve_field_updates(custom_fields, jira_instance)
        issue_dict.update(resolved_custom_fields)

    # Create the issue
    new_issue: Issue = jira_instance.create_issue(fields=issue_dict)  # pyright: ignore

    # Format response as markdown
    return f"JIRA Ticket Created Successfully {new_issue.key}"
