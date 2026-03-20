"""Tool for creating branches in GitHub repositories."""

from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github


class CreateBranchInput(BaseModel):
    """Input model for creating a new branch."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["swh", "software-factory"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo1", "xpad-shared"],
    )
    branch_name: str = Field(
        description="The name of the new branch to create.",
        examples=["feature/my-new-feature", "bugfix/fix-123", "release/v1.0.0"],
    )
    base_ref: str = Field(
        description=(
            "The reference (branch name, tag, or commit SHA) to base the new branch on. "
            "This is the starting point for the new branch."
        ),
        examples=["main", "develop", "abc123def456"],
    )


def create_branch(
    owner: str,
    repo: str,
    branch_name: str,
    base_ref: str,
    github: Github,
) -> str:
    """Create a new branch in a GitHub repository.

    Creates a new branch based on an existing reference (branch, tag, or commit).

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        branch_name: The name of the new branch to create.
        base_ref: The reference (branch name, tag, or commit SHA) to base the new branch on.
        github: GitHub instance for API access.

    Returns:
        Success message confirming the branch creation with commit details.

    Raises:
        Exception: If the base reference cannot be resolved or branch creation fails.
    """
    # Get the commit OID for the base reference
    commit = github.get_commit_for_expression(
        owner=owner,
        repo=repo,
        expression=base_ref,
        querydata="oid",
    )

    base_oid = commit.oid
    if base_oid is None:
        return f"Error: Could not resolve base reference '{base_ref}' to a commit."

    # Create the branch
    github.create_branch(
        owner=owner,
        repo=repo,
        base_oid=base_oid,
        ref_name=branch_name,
    )

    return (
        f"Successfully created branch '{branch_name}' in {owner}/{repo} based on '{base_ref}' (commit: {base_oid[:8]})"
    )
