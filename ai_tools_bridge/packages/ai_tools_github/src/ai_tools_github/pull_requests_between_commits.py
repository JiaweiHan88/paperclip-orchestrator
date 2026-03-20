"""Tool for finding pull requests between git commits."""

from datetime import timedelta

from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github
from ai_tools_github.models.pull_request import Commit

from .models.pull_request import PULL_REQUEST_GRAPHQL_QUERY, PullRequest, pull_request_list_to_markdown

COMMIT_QUERY = "oid committedDate"


class PullRequestsBetweenCommitsInput(BaseModel):
    """Input model for searching pull requests between two git commits."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["swh", "software-factory"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo1", "xpad-shared"],
    )
    branch: str = Field(
        description="The branch name to search in.",
        examples=["master", "main"],
    )
    start_commit_hash: str = Field(
        description="The starting commit hash (exclusive).",
        examples=["abc123", "def456"],
    )
    end_commit_hash: str = Field(
        description="The ending commit hash (inclusive).",
        examples=["ghi789", "jkl012"],
    )


def get_pull_requests_between_commits(
    owner: str,
    repo: str,
    branch: str,
    start_commit_hash: str,
    end_commit_hash: str,
    github: Github,
) -> str:
    """Get pull requests merged between two git commits.

    Finds all pull requests that were merged between the start and end commits
    on the specified branch. This is useful for root cause analysis when
    identifying which changes were introduced in a specific commit range.

    The tool:
        1. Fetches commit information for both start and end commits
        2. Determines the time range between the commits
        3. Searches for pull requests merged in that time range
        4. Filters out PRs that match the start commit to avoid duplicates

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        branch: The branch name to search in.
        start_commit_hash: The starting commit hash (exclusive).
        end_commit_hash: The ending commit hash (inclusive).
        github: GitHub instance for API access.

    Returns:
        Markdown formatted string listing all pull requests found between
        the commits, or a message if none are found.
    """
    try:
        prs = search_pull_requests_between_commits(
            github=github,
            owner=owner,
            repo=repo,
            branch=branch,
            start_commit_hash=start_commit_hash,
            end_commit_hash=end_commit_hash,
        )

        if not prs:
            return (
                f"No pull requests found between commits {start_commit_hash} and "
                f"{end_commit_hash} in {owner}/{repo} on branch {branch}."
            )

        return (
            f"Pull Requests between commits {start_commit_hash} and {end_commit_hash} "
            f"in {owner}/{repo} on branch {branch}:\n\n"
        ) + pull_request_list_to_markdown(prs)

    except Exception as e:
        return f"Error occurred while fetching pull requests between commits: {str(e)}"


def search_pull_requests_between_commits(
    github: Github,
    owner: str,
    repo: str,
    branch: str,
    start_commit_hash: str,
    end_commit_hash: str,
) -> list[PullRequest]:
    """
    Search for pull requests merged between two git commits.

    Args:
        github: GitHub client instance
        owner: Repository owner
        repo: Repository name
        branch: Branch name to search in
        start_commit_hash: Starting commit hash (exclusive)
        end_commit_hash: Ending commit hash (inclusive)

    Returns:
        List of PullRequest objects merged between the commits
    """
    # Get commit information using Github client
    try:
        start_commit: Commit = github.get_commit_for_expression(
            owner=owner,
            repo=repo,
            expression=start_commit_hash,
            querydata=COMMIT_QUERY,
        )
    except Exception as e:
        raise ValueError(f"Error getting start commit {start_commit_hash} from {owner}/{repo}: {e}") from e

    try:
        end_commit: Commit = github.get_commit_for_expression(
            owner=owner,
            repo=repo,
            expression=end_commit_hash,
            querydata=COMMIT_QUERY,
        )
    except Exception as e:
        raise ValueError(f"Error getting end commit {end_commit_hash} from {owner}/{repo}: {e}") from e

    if start_commit.oid == end_commit.oid:
        return []

    # Extract dates and create time range with 10 second buffer
    assert start_commit.committed_date, "Start commit must have a committed date"
    assert end_commit.committed_date, "End commit must have a committed date"
    start_date_str = (start_commit.committed_date - timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%S")
    end_date_str = (end_commit.committed_date + timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%S")

    return search_pull_requests_between_dates(
        github, owner, repo, branch, start_date_str, end_date_str, start_commit.oid
    )


def search_pull_requests_between_dates(
    github: Github,
    owner: str,
    repo: str,
    branch: str,
    start_date_str: str,
    end_date_str: str,
    exclude_commit_oid: str | None = None,
) -> list[PullRequest]:
    """
    Search for pull requests merged between two dates.

    Args:
        github: GitHub client instance
        owner: Repository owner
        repo: Repository name
        branch: Branch name to search in
        start_date_str: Start date in format YYYY-MM-DDTHH:MM:SS
        end_date_str: End date in format YYYY-MM-DDTHH:MM:SS
        exclude_commit_oid: Optional commit OID to exclude from results

    Returns:
        List of PullRequest objects merged in the date range
    """
    prs: list[PullRequest] = github.search_pull_requests(
        f"repo:{owner}/{repo} base:{branch} merged:{start_date_str}..{end_date_str}",
        querydata=PULL_REQUEST_GRAPHQL_QUERY,
        instance_class=PullRequest,  # type: ignore
    )

    # Remove PRs that have the excluded commit in their merge commit
    if exclude_commit_oid:
        prs = list(
            filter(
                lambda pr: pr.merge_commit.oid != exclude_commit_oid,  # type: ignore
                prs,
            )
        )

    return prs
