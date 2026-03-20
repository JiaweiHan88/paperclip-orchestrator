"""Backwards-compatible module for fetching open issues from a GitHub project board.

This module provides backwards compatibility for code that imports from open_issues.
The actual implementation has moved to issues_board.py with enhanced filtering support.

For new code, prefer using issues_board.get_issues_from_project_board() with filters.
"""

from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github

from .issues_board import get_issues_from_project_board as _get_issues_from_project_board


class IssueData(BaseModel):
    """Structure for issue data."""

    title: str = Field(description="The title of the issue")
    body: str = Field(description="The body/description of the issue")
    html_url: str = Field(description="The URL of the issue on GitHub")


class ProjectBoardIssuesOutput(BaseModel):
    """Output model for project board issues."""

    issues: list[IssueData] = Field(
        description="List of issues with title and body",
        default_factory=lambda: [],
    )


class ProjectBoardIssuesInput(BaseModel):
    """Input model for getting open issues from a GitHub project board."""

    project_url: str = Field(
        description="The URL of the GitHub project board.",
        examples=[
            "https://github.com/orgs/myorg/projects/1",
            "https://github.com/users/myuser/projects/2",
        ],
    )


def get_open_project_board_issues(
    project_url: str,
    github: Github,
) -> ProjectBoardIssuesOutput:
    """
    Fetch all open issues from a GitHub project board.

    This function retrieves all open issues from a specified GitHub project board.
    It is a backwards-compatible wrapper around get_issues_from_project_board().

    For more advanced filtering, use issues_board.get_issues_from_project_board()
    with the filters parameter.

    Args:
        project_url: The URL of the GitHub project board
                    (e.g., "https://github.com/orgs/myorg/projects/1")
        github: GitHub instance for API access

    Returns:
        ProjectBoardIssuesOutput containing a list of IssueData objects.

    Raises:
        Exception: If the project board cannot be accessed or issues cannot be retrieved

    Examples:
        >>> github = get_cc_github_instance("token")
        >>> result = get_open_project_board_issues(
        ...     "https://github.com/orgs/myorg/projects/1", github
        ... )
        >>> print(f"Found {len(result.issues)} open issues")
        Found 5 open issues
    """
    # Use the new implementation with status=open filter
    issues_list = _get_issues_from_project_board(
        project_url=project_url,
        github=github,
        filters={"status": "open"},
    )

    # Convert to the old format
    issues = [
        IssueData(
            title=issue.get("title", ""),
            body=issue.get("body", ""),
            html_url=issue.get("html_url", ""),
        )
        for issue in issues_list
    ]

    return ProjectBoardIssuesOutput(issues=issues)
