"""Tools for listing branches of a Gerrit project."""

from typing import Any

from pydantic import BaseModel, Field

from ai_tools_gerrit.gerrit_client import GerritClient, encode_project_name


class GetProjectBranchesInput(BaseModel):
    """Input for listing branches of a Gerrit project."""

    project: str = Field(
        description="Gerrit project name (may include slashes).",
        examples=["my/project"],
    )
    limit: int = Field(
        default=50,
        description="Maximum number of branches to return.",
        examples=[25, 50],
    )
    filter_regex: str | None = Field(
        default=None,
        description="Optional regex to filter branch names.",
        examples=["release.*"],
    )


def get_project_branches(
    project: str,
    gerrit: GerritClient,
    limit: int = 50,
    filter_regex: str | None = None,
) -> str:
    """List branches of a Gerrit project.

    Retrieves the list of branches for a project including revision
    information.

    Args:
        project: Gerrit project name.
        gerrit: Gerrit client instance.
        limit: Maximum number of branches to return.
        filter_regex: Optional regex to filter branch names.

    Returns:
        Formatted list of project branches with short SHAs.
    """
    encoded_project = encode_project_name(project)
    params: dict[str, Any] = {"n": str(limit)}
    if filter_regex:
        params["r"] = filter_regex

    branches: list[dict[str, Any]] = gerrit.get(f"/projects/{encoded_project}/branches/", params=params)

    if not branches:
        return f"No branches found for project '{project}'."

    output = f"Branches for {project} ({len(branches)} branches):\n"
    for branch_info in branches:
        ref: str = branch_info.get("ref", "?")
        revision: str = branch_info.get("revision", "?")
        short_rev = revision[:8] if len(revision) > 8 else revision

        display_name = ref
        if ref.startswith("refs/heads/"):
            display_name = ref[len("refs/heads/") :]
        elif ref == "HEAD":
            display_name = "HEAD"

        output += f"- {display_name} ({short_rev})\n"

    return output
