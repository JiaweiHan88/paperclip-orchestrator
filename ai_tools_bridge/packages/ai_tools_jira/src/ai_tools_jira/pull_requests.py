"""JIRA pull requests functionality."""

import re

from jira import JIRA
from pydantic import BaseModel, Field


class JiraPullRequestsInput(BaseModel):
    """Input model for getting pull requests associated with a JIRA issue.

    Args:
        issue_key: JIRA issue key (e.g., 'IPNDEV-23605').
    """

    issue_key: str = Field(
        description="JIRA issue key (e.g., 'IPNDEV-23605').",
        examples=["IPNDEV-23605", "SWH-456", "MCP-789"],
    )


def get_jira_pull_requests(
    issue_key: str,
    jira_instance: JIRA,
) -> str:
    """Get pull requests associated with a JIRA issue.

    Retrieves both formally linked pull requests (through Git integration plugins
    like GitKraken or GitHub) and pull request URLs mentioned in the issue
    description and comments.

    Args:
        issue_key: JIRA issue key (e.g., 'IPNDEV-23605').
        jira_instance: JIRA instance to use for the operation.

    Returns:
        Markdown formatted string containing pull request information,
        clearly distinguishing between linked and mentioned PRs.

    Raises:
        ValueError: If issue_key is empty.
        requests.HTTPError: If the Git plugin API request fails.
    """
    if not issue_key or not issue_key.strip():
        raise ValueError("Issue key cannot be empty.")

    # Get server URL from the JIRA instance
    server_url = jira_instance._options["server"]  # pyright: ignore

    # Get linked pull requests from Git plugin API
    api_url = f"{server_url}/rest/gitplugin/1.0/issuegitdetails/issue/{issue_key.strip()}/pullRequest"
    response = jira_instance._session.get(api_url)  # pyright: ignore
    response.raise_for_status()
    result = response.json()

    linked_prs: list[str] = []
    linked_pr_urls: set[str] = set()

    for item in result["pullRequests"]["items"]:
        url = item["url"]
        linked_pr_urls.add(url)
        linked_prs.append(f"- {url}: ({item['state']}) {item['title']}")

    # Get pull requests mentioned in text
    mentioned_pr_urls = _extract_pr_urls_from_text(issue_key, jira_instance)

    # Filter out mentioned PRs that are already linked
    mentioned_only_urls = mentioned_pr_urls - linked_pr_urls

    # Format output
    output_parts = [f"# Pull Requests for {issue_key}\n"]

    # Always show linked section
    output_parts.append("## Linked Pull Requests\n")
    if linked_prs:
        output_parts.append("\n".join(linked_prs))
    else:
        output_parts.append("No linked pull requests found.")

    # Always show mentioned section
    output_parts.append("\n\n## Pull Requests Mentioned in Text\n")
    if mentioned_only_urls:
        sorted_mentioned = sorted(mentioned_only_urls)
        output_parts.append("\n".join(f"- {url}" for url in sorted_mentioned))
    else:
        output_parts.append("No pull request URLs found in text.")

    return "\n".join(output_parts)


def _extract_pr_urls_from_text(issue_key: str, jira_instance: JIRA) -> set[str]:
    """Extract pull request URLs from issue description and comments.

    Args:
        issue_key: JIRA issue key.
        jira_instance: JIRA instance to use for the operation.

    Returns:
        Set of pull request URLs found in text.
    """
    # Regex patterns for common PR URL formats
    pr_patterns = [
        r"https?://github\.com/[\w\-\.]+/[\w\-\.]+/pull/\d+",
        r"https?://gitlab\.com/[\w\-\.]+/[\w\-\.]+/-/merge_requests/\d+",
        r"https?://bitbucket\.org/[\w\-\.]+/[\w\-\.]+/pull-requests/\d+",
        r"https?://dev\.azure\.com/[\w\-\.]+/[\w\-\.]+/_git/[\w\-\.]+/pullrequest/\d+",
        # Generic pattern for custom GitHub Enterprise, GitLab, etc.
        r"https?://[^/\s]+/[\w\-\.]+/[\w\-\.]+/(?:pull|merge_requests?|pull-requests?)/\d+",
    ]

    combined_pattern = "|".join(f"({pattern})" for pattern in pr_patterns)

    # Fetch the issue
    issue = jira_instance.issue(issue_key.strip(), fields="description,comment")

    pull_request_urls: set[str] = set()

    # Extract PRs from description
    if issue.fields.description:
        matches = re.findall(combined_pattern, issue.fields.description)
        for match_tuple in matches:
            for url in match_tuple:
                if url:
                    pull_request_urls.add(url)

    # Extract PRs from comments
    if hasattr(issue.fields, "comment") and issue.fields.comment:
        for comment in issue.fields.comment.comments:
            if comment.body:
                matches = re.findall(combined_pattern, comment.body)
                for match_tuple in matches:
                    for url in match_tuple:
                        if url:
                            pull_request_urls.add(url)

    return pull_request_urls
