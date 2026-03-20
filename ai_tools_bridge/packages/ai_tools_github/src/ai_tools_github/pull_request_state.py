import json
from typing import cast

import requests
from loguru import logger
from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github

from .models.pull_request import (
    PULL_REQUEST_GRAPHQL_QUERY,
    CheckRun,
    Label,
    PullRequest,
    Review,
    ReviewRequest,
    StatusContext,
    User,
)


def _get_required_status_checks_from_branch_protection(
    github: Github,
    owner: str,
    repo: str,
    branch: str,
) -> set[str]:
    """Get the required status check names from branch protection rules via REST API.

    Args:
        github: The Github instance to use for API calls.
        owner: The repository owner.
        repo: The repository name.
        branch: The branch name to check protection rules for.

    Returns:
        set[str]: Set of required status check context names.
    """
    logger.debug(f"Fetching branch protection rules for {owner}/{repo} on branch {branch}")

    try:
        response = github.v3_get(
            url_part=f"/repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks",
            update_headers={"Accept": "application/vnd.github.v3+json"},
        )
        # Parse JSON response
        commit_data = json.loads(response)
        required_checks = commit_data.get("contexts", [])
        logger.debug(f"Found {len(required_checks)} required status checks: {required_checks}")
        return set(required_checks)
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch branch protection rules for {branch}: {str(e)}")
        return set(f"Error occurred while fetching branch protection rules: {str(e)}")


class PullRequestStatusInput(BaseModel):
    """Input model for getting status of a github pull request."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["swh", "software-factory"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo1", "xpad-shared"],
    )
    number: int = Field(
        description="The number of the pull request.",
        examples=[134, 83733],
    )


def _format_status_checks(
    check_runs_status: list[CheckRun | StatusContext],
    required_check_names: set[str],
) -> str:
    """Format status checks section for markdown.

    Args:
        check_runs_status: List of check run or status context objects.
        required_check_names: Set of required status check names.

    Returns:
        str: Markdown formatted status checks section, or empty string if no checks.
    """
    logger.debug(f"Formatting {len(check_runs_status)} status checks with {len(required_check_names)} required")
    if not check_runs_status and not required_check_names:
        logger.debug("No status checks to format")
        return ""

    markdown = "### Status Checks:\n"

    # Collect names of existing checks
    existing_check_names: set[str] = set()
    for context in check_runs_status:
        if isinstance(context, CheckRun):
            if context.name is not None:
                existing_check_names.add(context.name)
        else:
            if context.context is not None:
                existing_check_names.add(context.context)

    # Show existing checks
    for context in check_runs_status:
        if isinstance(context, CheckRun):
            check_name = context.name
            completed_note = f" (completed at {context.completed_at})" if context.completed_at else ""
            conclusion = f" - {context.conclusion}" if context.conclusion else ""
            is_required = check_name in required_check_names
            is_required_str = " [REQUIRED]" if is_required else ""
            summary = f"\n#### Summary for {check_name}:\n{context.summary}" if context.summary else ""
            markdown += (
                f"### **{check_name}**{completed_note}: {context.status}{conclusion}{is_required_str}{summary}\n"
            )
        else:  # StatusContext
            check_name = context.context
            is_required = check_name in required_check_names
            is_required_str = " [REQUIRED]" if is_required else ""
            markdown += f"### **{check_name}**: {context.state}{is_required_str}\n"

    # Show missing required checks (haven't started yet)
    missing_required_checks = required_check_names - existing_check_names
    for missing_check in sorted(missing_required_checks):
        markdown += f"### **{missing_check}**: NOT STARTED [REQUIRED]\n"

    return markdown + "\n"


def _format_labels(labels: list[Label]) -> str:
    """Format labels section for markdown.

    Args:
        labels: List of label objects.

    Returns:
        str: Markdown formatted labels section, or empty string if no labels.
    """
    if not labels:
        return ""

    markdown = "### Labels:\n"
    for label in labels:
        markdown += f"- {label.name}\n"
    return markdown + "\n"


def _format_description(body: str | None) -> str:
    """Format description section for markdown.

    Args:
        body: The PR description body.

    Returns:
        str: Markdown formatted description section.
    """
    description = body or "No description provided."
    return f"### Description:\n{description}\n\n"


def _format_current_reviews(reviews: list[Review]) -> str:
    """Format current reviews section for markdown.

    Args:
        reviews: List of review objects.

    Returns:
        str: Markdown formatted current reviews section.
    """
    markdown = "### Current Reviews:\n"
    if reviews:
        for review in reviews:
            markdown += f"- **{review.author.login}**: {review.state} at {review.created_at}\n"
    else:
        markdown += "- None\n"
    return markdown + "\n"


def _format_missing_approvals(review_requests: list[ReviewRequest]) -> str:
    """Format missing approvals section for markdown.

    Args:
        review_requests: List of review request objects.

    Returns:
        str: Markdown formatted missing approvals section.
    """
    required_approvals = [req for req in review_requests if req.as_code_owner]
    markdown = "### Missing Approvals:\n"
    if required_approvals:
        for review_request in required_approvals:
            reviewer = review_request.requested_reviewer
            if reviewer is None:
                continue
            if isinstance(reviewer, User):
                reviewer_name = reviewer.login
            else:  # Team
                reviewer_name = reviewer.name
            markdown += f"- {reviewer_name}\n"
    else:
        markdown += "- None\n"
    return markdown + "\n"


def _determine_overall_status(pull_request: PullRequest) -> str:
    """Determine overall PR status string.

    Args:
        pull_request: The PullRequest object.

    Returns:
        str: Human-readable PR status.
    """
    if pull_request.merged:
        assert pull_request.merge_commit is not None, "Merge commit should be present for merged pull requests"
        return f"merged ({pull_request.merge_commit.oid})"
    if pull_request.closed:
        return "closed"

    review_state = pull_request.review_decision or "UNREVIEWED"
    mergeable_state = pull_request.mergeable or "UNKNOWN"
    return f"open {review_state} {mergeable_state}".capitalize()


def _determine_pr_state(pull_request: PullRequest) -> str:
    """Determine PR state (Draft, Merged, Closed, or Open).

    Args:
        pull_request: The PullRequest object.

    Returns:
        str: PR state string.
    """
    if pull_request.is_draft:
        return "Draft"
    if pull_request.merged:
        return "Merged"
    if pull_request.closed:
        return "Closed"
    return "Open"


def pull_request_state_to_markdown(
    pull_request: PullRequest,
    required_check_names: set[str] | None = None,
) -> str:
    """Convert required Pull Request data to a Markdown string.

    Args:
        pull_request: The PullRequest object to convert.
        required_check_names: Optional set of required status check names from branch protection.

    Returns:
        str: Markdown formatted string with PR state information.
    """
    logger.debug(f"Converting PR #{pull_request.number} to markdown")
    if required_check_names is None:
        required_check_names = set()
        logger.debug("No required check names provided")

    # Extract status checks from the latest commit
    check_runs_status = (
        pull_request.commits[-1].status_check_rollup.contexts
        if pull_request.commits and pull_request.commits[-1].status_check_rollup
        else []
    )

    # Build markdown sections
    markdown = "## Pull Request State Analysis\n\n"
    markdown += _format_status_checks(check_runs_status, required_check_names)
    markdown += _format_labels(pull_request.labels)
    markdown += _format_description(pull_request.body)
    markdown += _format_current_reviews(pull_request.reviews)
    markdown += _format_missing_approvals(pull_request.review_requests)

    # Add status information
    overall_status = _determine_overall_status(pull_request)
    pr_state = _determine_pr_state(pull_request)

    markdown += f"### Overall PR Status: {overall_status}\n\n"
    markdown += f"### Pull Request State: {pr_state}\n"
    markdown += f"### PR latest SHA commit: {pull_request.head_ref_oid}\n"

    return markdown


def get_pull_request_state(
    owner: str,
    repo: str,
    number: int,
    github: Github,
) -> str:
    """Get comprehensive information about a pull request's current state.

    Retrieves detailed PR information including required status checks,
    approvals, current reviews, missing approvals, labels, and description.
    Returns a formatted markdown summary suitable for display or further processing.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        number: The number of the pull request.
        github: The GitHub instance to use for API calls.

    Returns:
        Markdown formatted pull request state information including status checks,
        review status, labels, and overall PR state.

    Raises:
        Exception: If the pull request cannot be retrieved or accessed.
    """
    logger.info(f"Fetching PR state for {owner}/{repo}#{number}")
    # Use the standard query (isRequired via GraphQL doesn't work on all GitHub instances)
    pull_request = cast(
        PullRequest,
        github.pull_request(
            owner=owner,
            repo=repo,
            number=number,
            querydata=PULL_REQUEST_GRAPHQL_QUERY,
            instance_class=PullRequest,  # pyright: ignore
        ),
    )
    logger.debug(f"PR title: {pull_request.title}")

    # Get required status checks from branch protection rules via REST API
    base_branch = pull_request.base_ref_name or "main"
    logger.debug(f"Base branch: {base_branch}")
    required_check_names = _get_required_status_checks_from_branch_protection(
        github=github,
        owner=owner,
        repo=repo,
        branch=base_branch,
    )

    text = pull_request_state_to_markdown(pull_request, required_check_names)
    logger.info(f"Successfully generated PR state markdown for {owner}/{repo}#{number}")

    return text
