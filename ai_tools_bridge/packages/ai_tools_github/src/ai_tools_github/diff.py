from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github


class PullRequestDiffInput(BaseModel):
    """Input model for getting the diff of a pull request."""

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


def get_pull_request_diff(
    owner: str,
    repo: str,
    github: Github,
    number: int,
) -> str:
    """Get the diff content from a pull request.

    Retrieves the complete diff showing all file changes in the pull request.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        github: GitHub instance for API access.
        number: The number of the pull request.

    Returns:
        The diff content as a string showing all file changes.

    Raises:
        Exception: If the pull request does not exist or access is denied.
    """
    return github.pull_request_diff(owner, repo, number)
