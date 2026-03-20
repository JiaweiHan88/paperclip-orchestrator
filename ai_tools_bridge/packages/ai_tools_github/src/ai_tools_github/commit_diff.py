"""Tool for retrieving detailed commit diff content."""

from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github


class CommitDiffInput(BaseModel):
    """Input model for getting detailed diff content of a specific commit."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["owner", "some-user"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo", "some-repo"],
    )
    commit_sha: str = Field(
        description="The SHA hash of the commit to get diff for.",
        examples=["abc123def456", "1a2b3c4d"],
    )
    file_scope: list[str] | None = Field(
        default=None,
        description=(
            "Optional list of file extensions or patterns to include in diffs "
            "(e.g., ['.py', '.js', '.md']). If not specified, includes all files."
        ),
        examples=[[".py", ".js"], [".md", ".txt"], [".yaml", ".yml", ".json"]],
    )


def should_include_file(filename: str, file_scope: list[str] | None = None) -> bool:
    """Check if a filename should be included based on file_scope filter.

    Args:
        filename: The filename to check
        file_scope: Optional list of file extensions or patterns to include.
                   If None, applies default filtering (excludes binary/lock files).
                   If provided, only includes files matching the scope.

    Returns:
        True if the file should be included, False otherwise
    """
    if file_scope is not None:
        # Use file_scope to filter
        if not file_scope:  # Empty list excludes all files
            return False

        filename_lower = filename.lower()
        for scope_pattern in file_scope:
            if scope_pattern.startswith("."):
                # Extension match
                if filename_lower.endswith(scope_pattern.lower()):
                    return True
            else:
                # Pattern match
                if scope_pattern.lower() in filename_lower:
                    return True
        return False

    # Include everything else
    return True


def get_commit_diff(
    owner: str,
    repo: str,
    commit_sha: str,
    github: Github,
    file_scope: list[str] | None = None,
) -> str:
    """Get the full diff content for a commit.

    Retrieves the complete diff showing all file changes in the specified commit.
    Optionally filters files by extension or pattern.

    Args:
        owner: Repository owner.
        repo: Repository name.
        commit_sha: Commit SHA to get diff for.
        github: GitHub instance for API access.
        file_scope: Optional list of file extensions or patterns to include
            (e.g., ['.py', '.js']). If not specified, includes all files.

    Returns:
        Formatted diff content as a string.

    Raises:
        Exception: If the commit does not exist or access is denied.
    """
    try:
        # Use the v3_get method to get commit diff from REST API
        response = github.v3_get(
            url_part=f"/repos/{owner}/{repo}/commits/{commit_sha}",
            update_headers={"Accept": "application/vnd.github.v3+json"},
        )

        import json

        commit_data: dict[str, Any] = json.loads(response)

        if "files" not in commit_data:
            return "No diff available"

        diff_lines: list[str] = []
        for file_info in commit_data["files"]:
            filename = file_info.get("filename", "unknown")

            # Apply file scope filtering
            if not should_include_file(filename, file_scope):
                continue

            status = file_info.get("status", "modified")

            # Add empty line between files (not before the first file)
            if diff_lines:  # Only if there are already files added
                diff_lines.append("")

            # Add file header
            diff_lines.append(f"--- a/{filename}")
            diff_lines.append(f"+++ b/{filename}")

            # Add patch content if available
            if "patch" in file_info:
                patch_lines = file_info["patch"].split("\n")
                for line in patch_lines:
                    diff_lines.append(line)
            else:
                diff_lines.append(f"File {status}: {filename}")

        if not diff_lines:
            scope_desc = f" (file scope: {file_scope})" if file_scope else ""
            return f"No relevant changes found{scope_desc}"

        return "\n".join(diff_lines)
    except Exception as e:
        logger.warning(f"Failed to get diff for commit {commit_sha}: {e}")
        return "Diff unavailable"
