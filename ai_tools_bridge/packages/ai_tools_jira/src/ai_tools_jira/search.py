"""JIRA search functionality."""

from ai_tools_base import LoggingInterface
from jira import JIRA
from pydantic import BaseModel, Field

from .markdown_renderer import render_issue_to_markdown


class JiraSearchInput(BaseModel):
    """Input model for searching JIRA issues using JQL.

    Args:
        query: JQL query string to search for issues.
        fields: Comma-separated list of fields to return in the results.
    """

    query: str = Field(
        description="JQL query string to search for issues.",
        examples=[
            "project = PROJECT AND status = 'In Progress'",
            "assignee = currentUser() AND status != Done",
            "created >= -7d AND priority = High",
        ],
    )


def search_jira(
    query: str,
    jira_instance: JIRA,
    logging: LoggingInterface,
) -> str:
    """Search JIRA issues using JQL and return formatted results.

    Args:
        query: JQL query string to search for issues.
        jira_instance: JIRA instance to use for the search.
        logging: Logging interface for progress reporting.

    Returns:
        Markdown formatted string containing JIRA issue details, with count
        of total and displayed results.

    Raises:
        ValueError: If query is empty or contains only whitespace.
        Exception: If JIRA API call fails.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    logging.info(f"Searching JIRA with query: {query}")

    try:
        issues = jira_instance.search_issues(query.strip())
    except Exception as e:
        logging.error(f"JIRA search failed: {e}")
        raise Exception(f"JIRA search failed: {e}") from e

    if not issues:
        logging.info("No JIRA issues found for the query")
        return "# JIRA Search Results\n\nNo issues found for the query."

    # Get total count from the result list
    total_count = issues.total if hasattr(issues, "total") else len(issues)

    issue_texts: list[str] = []
    for issue in issues:
        issue_texts.append(render_issue_to_markdown(issue))

    logging.info(f"Successfully retrieved {len(issue_texts)} out of {total_count} JIRA issues")

    # Build result with header showing count
    result = f"# JIRA Search Results\n\n**Found {total_count} issues** (showing {len(issue_texts)})\n\n---\n\n"
    result += "\n\n---\n\n".join(issue_texts)
    return result
