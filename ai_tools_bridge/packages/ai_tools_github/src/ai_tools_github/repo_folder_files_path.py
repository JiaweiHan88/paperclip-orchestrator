"""Tool for retrieving GitHub repository file tree structure with links."""

import json

from loguru import logger
from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github


class RepoFolderFilesPathInput(BaseModel):
    """Input model for getting the file tree structure of a repository."""

    owner: str = Field(
        description="The owner of the GitHub repository.",
        examples=["octocat", "microsoft", "tensorflow"],
    )
    repo: str = Field(
        description="The name of the GitHub repository.",
        examples=["Hello-World", "vscode", "tensorflow"],
    )
    ref: str = Field(
        default="HEAD",
        description="The git reference (branch, tag, or commit) to get the tree from.",
        examples=["main", "HEAD", "v1.0.0", "feature-branch"],
    )
    folder_path: str = Field(
        default="",
        description="The folder path within the repository to get the tree from.",
        examples=["src/", "docs/", "lib/utils/"],
    )


def _normalize_folder_path(folder_path: str) -> str:
    """Normalize folder path to ensure it ends with / if non-empty.

    Args:
        folder_path: The folder path to normalize.

    Returns:
        str: Normalized folder path ending with /, or empty string if input was empty.
    """
    if folder_path and not folder_path.endswith("/"):
        return folder_path + "/"
    return folder_path


def _parse_tree_response(response: str) -> list[dict[str, str]]:
    """Parse GitHub tree API response.

    Args:
        response: JSON string response from GitHub API.

    Returns:
        list[dict[str, str]]: List of tree items with path and type.

    Raises:
        KeyError: If response doesn't contain expected tree data.
    """
    tree_data = json.loads(response)
    if "tree" not in tree_data:
        logger.error(f"No tree data found in response: {tree_data}")
        raise KeyError("No tree data found in response")
    return tree_data["tree"]


def _collect_files_in_folder(
    tree_items: list[dict[str, str]],
    folder_path: str,
) -> list[str]:
    """Collect all files (blobs) within the specified folder.

    Args:
        tree_items: List of tree items from GitHub API.
        folder_path: The folder path to filter files from.

    Returns:
        list[str]: Sorted list of file paths within the folder.
    """
    files_in_folder: list[str] = []
    for item in tree_items:
        path = item.get("path", "")
        item_type = item.get("type", "blob")

        # Only include blobs (files) that are in the specified folder
        if item_type == "blob" and path.startswith(folder_path):
            files_in_folder.append(path)

    return sorted(files_in_folder)


def _build_markdown_output(
    owner: str,
    repo: str,
    ref: str,
    folder_path: str,
    files: list[str],
) -> str:
    """Build markdown formatted output for file list.

    Args:
        owner: Repository owner.
        repo: Repository name.
        ref: Git reference used.
        folder_path: The folder path queried.
        files: List of file paths to include in output.

    Returns:
        str: Markdown formatted output.
    """
    output_lines: list[str] = []
    output_lines.append(f"# Files in {owner}/{repo}/{folder_path}")
    output_lines.append(f"**Reference:** {ref}")
    output_lines.append(f"**Total Files:** {len(files)}")
    output_lines.append("")

    if not files:
        output_lines.append("No files found in this folder.")
        return "\n".join(output_lines)

    output_lines.append("## Files")
    output_lines.append("")

    for file_path in files:
        output_lines.append(f"- {file_path}")

    return "\n".join(output_lines)


def get_repo_folder_files_path(
    owner: str,
    repo: str,
    github: Github,
    ref: str = "HEAD",
    folder_path: str = "",
) -> str:
    """Get the list of file paths inside a specific folder in a repository.

    Retrieves all files within the specified folder path and returns them
    as a markdown-formatted list with their relative paths.

    Args:
        owner: The repository owner.
        repo: The repository name.
        github: GitHub instance for API access.
        ref: Git reference (branch, tag, or commit) to query.
        folder_path: The folder path to list files from (e.g., "zuul.d/pipelines/").

    Returns:
        Markdown-formatted string with file paths within the folder.

    Raises:
        Exception: If the repository cannot be accessed or the tree cannot be retrieved.
    """
    # Normalize folder path to ensure it ends with /
    normalized_folder_path = _normalize_folder_path(folder_path)

    try:
        # Get the repository tree using REST API
        response = github.v3_get(
            url_part=f"/repos/{owner}/{repo}/git/trees/{ref}",
            update_headers={"Accept": "application/vnd.github.v3+json"},
            params={"recursive": "1"},  # Get full recursive tree
        )

        # Parse the response and collect files
        tree_items = _parse_tree_response(response)
        files = _collect_files_in_folder(tree_items, normalized_folder_path)

        logger.info(f"Found {len(files)} files in folder: {normalized_folder_path}")

        # Build and return markdown output
        return _build_markdown_output(owner, repo, ref, normalized_folder_path, files)

    except KeyError:
        # Handle missing tree data
        return "No tree data found or repository is empty."
    except Exception as e:
        logger.error(f"Error fetching folder files: {str(e)}")
        return f"Error fetching folder files: {str(e)}"
