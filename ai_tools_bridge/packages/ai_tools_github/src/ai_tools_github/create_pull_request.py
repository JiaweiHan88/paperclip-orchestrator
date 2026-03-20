"""Tool for creating pull requests in GitHub repositories."""

from typing import cast

from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github

from .models.pull_request import (
    PullRequest,
)


class CreatePullRequestInput(BaseModel):
    """Input model for creating a pull request."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["swh", "software-factory"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo1", "xpad-shared"],
    )
    head_ref_name: str = Field(
        description=(
            "The name of the branch containing the changes (source branch). "
            "For cross-repository PRs, use the format 'owner:branch'."
        ),
        examples=["feature/my-feature", "bugfix/fix-123", "fork-owner:feature-branch"],
    )
    base_ref_name: str = Field(
        description="The name of the branch to merge into (target branch).",
        examples=["main", "develop", "release/v1.0"],
    )
    title: str = Field(
        description="The title of the pull request.",
        examples=["Add new feature X", "Fix bug in authentication", "Update documentation"],
    )
    body: str | None = Field(
        default=None,
        description="The body/description of the pull request (optional). Do not escape newlines or backslashes.",
        examples=[
            "## Summary\nThis PR adds a new feature that...\n\n## Changes\n- Added X\n- Modified Y",
            None,
        ],
    )
    draft: bool = Field(
        default=False,
        description="Whether to create the pull request as a draft.",
    )


def create_pull_request(
    owner: str,
    repo: str,
    head_ref_name: str,
    base_ref_name: str,
    title: str,
    github: Github,
    body: str | None = None,
    draft: bool = False,
) -> str:
    """Create a new pull request in a GitHub repository.

    Opens a pull request to merge changes from the head branch into the base branch.
    Supports creating draft pull requests for work in progress.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        head_ref_name: The name of the branch containing the changes (source branch).
            For cross-repository PRs, use the format 'owner:branch'.
        base_ref_name: The name of the branch to merge into (target branch).
        title: The title of the pull request.
        github: GitHub instance for API access.
        body: The body/description of the pull request (optional).
        draft: Whether to create the pull request as a draft.

    Returns:
        Markdown formatted information about the created pull request, including URL.

    Raises:
        Exception: If the repository ID cannot be retrieved or PR creation fails.
    """
    # Get the repository ID
    repository = github.get_repository(owner, repo, "id")
    repository_id = repository.id

    if repository_id is None:
        return f"Error: Could not get repository ID for {owner}/{repo}"

    # Create the pull request
    pull_request = github.create_pull_request(
        repository_id=repository_id,
        head_ref_name=head_ref_name,
        base_ref_name=base_ref_name,
        title=title,
        body=body,
        draft=draft,
        querydata="url",
    )

    if pull_request is None:
        return (
            f"Pull request created in {owner}/{repo}\n"
            f"**Title:** {title}\n"
            f"**Source:** {head_ref_name} → **Target:** {base_ref_name}"
        )

    # Convert to our PullRequest model and format
    pr = cast(PullRequest, pull_request)
    return f"Pull request created: {pr.url}"
