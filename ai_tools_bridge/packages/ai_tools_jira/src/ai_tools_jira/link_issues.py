"""Link JIRA issues functionality."""

from jira import JIRA
from pydantic import BaseModel, Field


class LinkJiraIssuesInput(BaseModel):
    """Input model for linking two JIRA issues.

    Args:
        inward_issue: The issue key that will be the inward/source of the link (e.g., 'PROJ-123').
        outward_issue: The issue key that will be the outward/target of the link (e.g., 'PROJ-456').
        link_type: The type of link relationship.
    """

    inward_issue: str = Field(
        description="The issue key that will be the inward/source of the link (e.g., 'PROJ-123').",
        examples=["ORIONINIT-163931", "SWH-456"],
    )
    outward_issue: str = Field(
        description="The issue key that will be the outward/target of the link (e.g., 'PROJ-456').",
        examples=["ORIONINIT-163077", "MCP-789"],
    )
    link_type: str = Field(
        description="The type of link. Common types: 'blocks', 'clones', 'duplicates', 'relates', 'causes'.",
        examples=["causes", "blocks", "relates", "duplicates"],
        default="relates",
    )


def link_jira_issues(
    inward_issue: str,
    outward_issue: str,
    jira_instance: JIRA,
    link_type: str = "relates",
) -> str:
    """Create a link between two JIRA issues.

    Establishes a relationship between two issues using the specified link type.
    Common link types include 'blocks', 'clones', 'duplicates', 'relates', and 'causes'.

    Args:
        inward_issue: The inward/source issue key (e.g., 'PROJ-123').
        outward_issue: The outward/target issue key (e.g., 'PROJ-456').
        jira_instance: JIRA instance to use for the operation.
        link_type: The type of relationship (default: 'relates').

    Returns:
        Success message confirming the link was created.

    Raises:
        jira.exceptions.JIRAError: If either issue does not exist, the link type
            is invalid, or permission is denied.
    """
    jira_instance.create_issue_link(type=link_type, inwardIssue=inward_issue, outwardIssue=outward_issue)  # pyright: ignore

    return f"✅ Successfully linked {inward_issue} {link_type.lower()} {outward_issue}"
