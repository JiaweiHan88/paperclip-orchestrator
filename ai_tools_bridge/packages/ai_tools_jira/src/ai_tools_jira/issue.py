from jira import JIRA
from pydantic import BaseModel, Field

from .markdown_renderer import render_issue_to_markdown


class JiraIssueInput(BaseModel):
    """Input model for getting details of a Jira issue.

    Args:
        key: The key of the Jira issue (e.g., 'PROJECT-123').
        fields: Optional list of field names or IDs to include beyond standard fields.
                If None (default), only standard fields are shown.
                If empty list [], all available fields are shown.
                If list of field names, those additional fields are included with standard fields.
                Use get_jira_fields tool to discover available fields.
    """

    key: str = Field(
        description="The key of the Jira issue (e.g., 'PROJECT-123').",
        examples=["SWH-456", "MCP-789"],
    )
    fields: list[str] | None = Field(
        default=None,
        description=(
            "Optional list of field names or IDs to include. "
            "None (default) = standard fields only, "
            "[] (empty list) = all fields, "
            "['field1', 'field2'] = standard fields + specified fields."
        ),
        examples=[["labels", "components"], ["Epic Link", "customfield_10500"], []],
    )


def get_jira_issue(
    key: str,
    jira_instance: JIRA,
    fields: list[str] | None = None,
) -> str:
    """Fetch and format details of a JIRA issue given its key.

    Args:
        key: The key of the JIRA issue (e.g., 'PROJ-123').
        jira_instance: JIRA instance to use for the operation.
        fields: Optional list of field names or IDs to include.
            None (default) = standard fields only,
            [] (empty list) = all available fields,
            ['field1', 'field2'] = standard fields + specified fields.

    Returns:
        Markdown formatted string with issue details.

    Raises:
        jira.exceptions.JIRAError: If the issue does not exist or access is denied.
    """
    issue = jira_instance.issue(key)

    return render_issue_to_markdown(
        issue,
        jira_instance=jira_instance,
        fields=fields,
    )
