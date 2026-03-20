"""Pull request action tools for adding comments and managing labels."""

from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github
from ai_tools_github.github_types import Reaction


class AddCommentToPullRequestInput(BaseModel):
    """Input model for adding a comment to a pull request."""

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
    body: str = Field(
        description="The body of the comment (supports markdown).",
        examples=["Great work!", "LGTM :+1:"],
    )


def add_comment_to_pull_request(
    owner: str,
    repo: str,
    number: int,
    body: str,
    github: Github,
) -> str:
    """Add a comment to a pull request.

    Posts a new comment on the specified pull request. The comment body
    supports markdown formatting.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        number: The number of the pull request.
        body: The body of the comment (supports markdown).
        github: GitHub instance for API access.

    Returns:
        URL of the created comment.

    Raises:
        ValueError: If the pull request ID cannot be retrieved.
        Exception: If the comment creation fails.
    """
    pr = github.pull_request(owner, repo, number, querydata="id")

    if pr.id is None:
        msg = f"Could not get ID for PR #{number} in {owner}/{repo}"
        raise ValueError(msg)

    commend_node_id = github.add_comment(subject_id=pr.id, body=body)
    comment_url = github.get_comment_url(commend_node_id)  # TODO Make add_comment directly output this information
    return comment_url


class CreateReactionToPullRequestCommentInput(BaseModel):
    """Input model for creating a reaction to a pull request comment."""

    comment_node_id: str = Field(
        description="The node ID of the comment to add a reaction to.",
        examples=["IC_kwDOABCDE123456789", "MDEyOklzc3VlQ29tbWVudDEyMzQ1Njc4OQ=="],
    )
    reaction: Reaction = Field(
        description="The type of reaction to add.",
        examples=["+1", "heart", "rocket"],
    )


def create_reaction_to_pull_request_comment(
    comment_node_id: str,
    reaction: Reaction,
    github: Github,
) -> str:
    """Create a reaction on a pull request comment.

    Adds an emoji reaction to an existing comment on a pull request.

    Args:
        comment_node_id: The node ID of the comment to add a reaction to.
        reaction: The type of reaction to add (e.g., '+1', 'heart', 'rocket').
        github: GitHub instance for API access.

    Returns:
        URL of the comment that received the reaction.

    Raises:
        Exception: If the reaction creation fails.
    """
    github.create_reaction(subject_id=comment_node_id, content=reaction)
    comment_url = github.get_comment_url(comment_node_id)  # TODO Make create_reaction directly output this information

    return comment_url


class AddLabelToPullRequestInput(BaseModel):
    """Input model for adding labels to a pull request."""

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
    label_names: list[str] = Field(
        description="The names of the labels to add to the pull request.",
        examples=[["bug", "enhancement"], ["needs-review"]],
    )


def add_label_to_pull_request(
    owner: str,
    repo: str,
    number: int,
    label_names: list[str],
    github: Github,
) -> str:
    """Add labels to a pull request.

    Attaches one or more labels to the specified pull request. Labels must
    already exist in the repository.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        number: The number of the pull request.
        label_names: The names of the labels to add.
        github: GitHub instance for API access.

    Returns:
        Confirmation message listing the added labels.

    Raises:
        ValueError: If the pull request ID cannot be retrieved or any
            specified labels do not exist in the repository.
        Exception: If the label addition fails.
    """
    pr = github.pull_request(owner, repo, number, querydata="id")

    if pr.id is None:
        msg = f"Could not get ID for PR #{number} in {owner}/{repo}"
        raise ValueError(msg)

    label_ids: list[str] = []
    not_found_labels: list[str] = []

    for label_name in label_names:
        label_id = github.get_label_id(owner, repo, label_name)
        if label_id is None:
            not_found_labels.append(label_name)
        else:
            label_ids.append(label_id)

    if not_found_labels:
        msg = f"Labels not found in {owner}/{repo}: {', '.join(not_found_labels)}"
        raise ValueError(msg)

    github.add_label_to_labelable(labelable_id=pr.id, label_ids=label_ids)

    labels_str = ", ".join(label_names)
    return f"Successfully added labels [{labels_str}] to PR #{number} in {owner}/{repo}."


class RemoveLabelFromPullRequestInput(BaseModel):
    """Input model for removing labels from a pull request."""

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
    label_names: list[str] = Field(
        description="The names of the labels to remove from the pull request.",
        examples=[["bug", "wontfix"], ["needs-review"]],
    )


def remove_label_from_pull_request(
    owner: str,
    repo: str,
    number: int,
    label_names: list[str],
    github: Github,
) -> str:
    """Remove labels from a pull request.

    Removes one or more labels from the specified pull request.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        number: The number of the pull request.
        label_names: The names of the labels to remove.
        github: GitHub instance for API access.

    Returns:
        Confirmation message listing the removed labels.

    Raises:
        ValueError: If the pull request ID cannot be retrieved or any
            specified labels do not exist in the repository.
        Exception: If the label removal fails.
    """
    pr = github.pull_request(owner, repo, number, querydata="id")

    if pr.id is None:
        msg = f"Could not get ID for PR #{number} in {owner}/{repo}"
        raise ValueError(msg)

    label_ids: list[str] = []
    not_found_labels: list[str] = []

    for label_name in label_names:
        label_id = github.get_label_id(owner, repo, label_name)
        if label_id is None:
            not_found_labels.append(label_name)
        else:
            label_ids.append(label_id)

    if not_found_labels:
        msg = f"Labels not found in {owner}/{repo}: {', '.join(not_found_labels)}"
        raise ValueError(msg)

    github.remove_label_from_labelable(labelable_id=pr.id, label_ids=label_ids)

    labels_str = ", ".join(label_names)
    return f"Successfully removed labels [{labels_str}] from PR #{number} in {owner}/{repo}."
