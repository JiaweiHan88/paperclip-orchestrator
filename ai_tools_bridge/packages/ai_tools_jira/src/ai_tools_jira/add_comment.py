"""Add comment to JIRA ticket functionality."""

from jira import JIRA, Issue
from pydantic import BaseModel, Field

from .markup_converter import markdown_to_jira


class AddJiraCommentInput(BaseModel):
    """Input model for adding a comment to an existing JIRA ticket.

    Args:
        issue_key: The JIRA issue key (e.g., 'PROJ-123').
        comment: The comment text to add to the ticket.
    """

    issue_key: str = Field(
        description="The JIRA issue key (e.g., 'PROJ-123').",
        examples=["SWH-123", "MCP-456", "PROJ-789"],
    )
    comment: str = Field(
        description=(
            "The comment text to add to the ticket. "
            "Markdown formatting will be automatically converted to JIRA wiki markup. "
            "Supports headers (##), bold (**text**), bullets (-), numbered lists (1.), "
            "inline code (`code`), and code blocks (```)."
        ),
        examples=[
            "This issue has been reviewed and approved for development.",
            "Updated the implementation based on feedback.",
            "Tested successfully in development environment.",
        ],
    )


def add_jira_comment(
    issue_key: str,
    comment: str,
    jira_instance: JIRA,
) -> str:
    """Add a comment to an existing JIRA ticket.

    The comment will be automatically converted from markdown to JIRA wiki markup format.
    This allows you to use familiar markdown syntax which will be properly displayed in JIRA.

    Args:
        issue_key: The JIRA issue key (e.g., 'PROJ-123').
        comment: The comment text to add to the ticket (markdown format supported).
        jira_instance: JIRA instance to use for the operation.

    Returns:
        Success message confirming the comment was added.

    Raises:
        jira.exceptions.JIRAError: If the issue does not exist or access is denied.
    """
    # Get the existing issue to verify it exists
    issue: Issue = jira_instance.issue(issue_key)  # pyright: ignore

    # Convert markdown to JIRA wiki markup
    jira_comment = markdown_to_jira(comment)

    # Add the comment to the issue
    jira_instance.add_comment(issue, jira_comment)  # pyright: ignore

    # Format response as markdown
    return f"Comment added successfully to JIRA ticket {issue_key}"
