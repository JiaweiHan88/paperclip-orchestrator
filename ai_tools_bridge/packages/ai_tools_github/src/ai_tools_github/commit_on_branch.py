"""Tool for creating commits on branches in GitHub repositories."""

from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github
from ai_tools_github.github_types import FileAddition, FileDeletion


class FileAdditionInput(BaseModel):
    """A file to add or modify in the commit."""

    path: str = Field(
        description="The path of the file in the repository.",
        examples=["src/main.py", "README.md", "config/settings.json"],
    )
    content: str = Field(
        description="The content of the file (plain text, will be base64 encoded automatically).",
        examples=["print('Hello, World!')", "# My Project\n\nThis is a readme."],
    )


class FileDeletionInput(BaseModel):
    """A file to delete in the commit."""

    path: str = Field(
        description="The path of the file to delete in the repository.",
        examples=["old_file.py", "deprecated/config.json"],
    )


class CreateCommitOnBranchInput(BaseModel):
    """Input model for creating a commit on a branch."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["swh", "software-factory"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo1", "xpad-shared"],
    )
    branch_name: str = Field(
        description="The name of the branch to commit to.",
        examples=["feature/my-feature", "main", "develop"],
    )
    message_headline: str = Field(
        description="The headline (first line) of the commit message.",
        examples=["Add new feature", "Fix bug in login", "Update documentation"],
    )
    message_body: str | None = Field(
        default=None,
        description="The body of the commit message (optional, for detailed description).",
        examples=["This commit adds a new feature\nthat allows users to...", None],
    )
    additions: list[FileAdditionInput] | None = Field(
        default=None,
        description="List of files to add or modify in this commit.",
    )
    deletions: list[FileDeletionInput] | None = Field(
        default=None,
        description="List of files to delete in this commit.",
    )


def create_commit_on_branch(
    owner: str,
    repo: str,
    branch_name: str,
    message_headline: str,
    github: Github,
    additions: list[FileAdditionInput] | None = None,
    deletions: list[FileDeletionInput] | None = None,
    message_body: str | None = None,
) -> str:
    """Create a commit on a specified branch with file changes.

    Creates a new commit on the specified branch with the given file additions
    and/or deletions. At least one file change must be provided.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        branch_name: The name of the branch to commit to.
        message_headline: The headline (first line) of the commit message.
        github: GitHub instance for API access.
        additions: List of files to add or modify.
        deletions: List of files to delete.
        message_body: The body of the commit message (optional).

    Returns:
        A message with the result of the commit creation including commit SHA.

    Raises:
        ValueError: If both additions and deletions are empty or None.
        Exception: If the commit cannot be created due to API errors.
    """
    # Validate that at least one file change is provided
    has_additions = additions is not None and len(additions) > 0
    has_deletions = deletions is not None and len(deletions) > 0

    if not has_additions and not has_deletions:
        raise ValueError(
            "Cannot create a commit without any file changes. At least one file addition or deletion must be provided."
        )

    # Get the current HEAD SHA of the branch
    commit = github.get_commit_for_expression(
        owner=owner,
        repo=repo,
        expression=branch_name,
        querydata="oid",
    )

    head_sha = commit.oid
    if head_sha is None:
        return f"Error: Could not resolve branch '{branch_name}' to a commit."

    # Convert input models to local types
    file_additions: list[FileAddition] = []
    if additions:
        for addition in additions:
            file_additions.append(FileAddition.from_plain_text(addition.path, addition.content))

    file_deletions: list[FileDeletion] = []
    if deletions:
        for deletion in deletions:
            file_deletions.append(FileDeletion(path=deletion.path))

    # Create the commit
    result = github.create_commit_on_branch(
        owner=owner,
        repo=repo,
        ref_name=branch_name,
        head_sha=head_sha,
        message_headline=message_headline,
        message_body=message_body,
        additions=file_additions,
        deletions=file_deletions,
        querydata="oid messageHeadline",
    )

    if result is None:
        return f"Commit created on branch '{branch_name}' in {owner}/{repo}"

    return (
        f"Successfully created commit on branch '{branch_name}' in {owner}/{repo}\n"
        f"**Commit SHA:** `{result.oid}`\n"
        f"**Message:** {result.message_headline}"
    )
