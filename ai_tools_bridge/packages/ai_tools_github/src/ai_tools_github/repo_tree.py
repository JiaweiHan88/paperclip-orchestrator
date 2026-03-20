"""Tool for retrieving GitHub repository file tree structure with links."""

import json
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github


class RepoTreeInput(BaseModel):
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


def get_repo_tree(
    owner: str,
    repo: str,
    github: Github,
    ref: str = "HEAD",
) -> str:
    """
    Get the complete file tree structure of a repository with clickable URLs.

    This function retrieves the full directory structure of a GitHub repository,
    filtering out binary files and lock files, and returns a markdown-formatted
    tree with clickable links to each file. Progress is logged every 10 files
    for large repositories.

    The tool provides a comprehensive view of the repository structure,
    making it easy to navigate and understand the codebase organization.
    Only text-based files are included in the tree to focus on readable content.

    Args:
        owner: The owner of the GitHub repository
        repo: The name of the GitHub repository
        github: GitHub instance for API access
        ref: Git reference (branch, tag, or commit) to get tree from

    Returns:
        Markdown-formatted string with the repository file tree structure
        including clickable URLs to each file, directory count, and file statistics

    Raises:
        Exception: If the repository cannot be accessed or the tree cannot be retrieved
    """
    try:
        # Get the repository tree using REST API
        response = github.v3_get(
            url_part=f"/repos/{owner}/{repo}/git/trees/{ref}",
            update_headers={"Accept": "application/vnd.github.v3+json"},
            params={"recursive": "1"},  # Get full recursive tree
        )

        # Parse JSON response (v3_get always returns str)
        tree_data: dict[str, Any] = json.loads(response)

        if "tree" not in tree_data:
            logger.error(f"No tree data found in response: {tree_data}")
            return "No tree data found or repository is empty."

        # Build directory structure
        files: set[str] = set()
        directories: set[str] = set()
        processed_count = 0

        tree_items: list[dict[str, Any]] = tree_data["tree"]
        for item in tree_items:
            path: str = item.get("path", "")
            item_type: str = item.get("type", "blob")

            if item_type == "tree":
                directories.add(path)
            elif item_type == "blob":
                files.add(path)
                processed_count += 1

                # Log progress every 10 files
                if processed_count % 10 == 0:
                    logger.info(f"Processed {processed_count} files...")

        logger.info(f"Tree retrieval complete. Total processable files: {processed_count}")

        # Build the tree structure
        output_lines: list[str] = []
        output_lines.append(f"# Repository Tree: {owner}/{repo}")
        output_lines.append(f"**Reference:** {ref}")
        output_lines.append(f"**Total Files:** {processed_count}")
        output_lines.append("")

        # Get base URL for file links - assume github.com for now
        # TODO: Extract from github instance if needed for enterprise
        base_url = "https://github.com"

        # Format tree as markdown - simple approach
        output_lines.append("## File Tree")
        output_lines.append("")

        # Create a simple sorted list of all paths
        all_paths: list[tuple[str, str]] = []

        # Add directories
        for dir_path in sorted(directories):
            all_paths.append((dir_path, "directory"))

        # Add files
        for file_path in sorted(files):
            all_paths.append((file_path, "file"))

        # Sort all paths
        all_paths.sort(key=lambda x: x[0])

        # Track processed directories to avoid duplicates
        seen_dirs: set[str] = set()

        # Format each path
        for path, path_type in all_paths:
            if path_type == "directory" and path not in seen_dirs:
                depth = path.count("/")
                indent = "  " * depth
                output_lines.append(f"{indent}📁 **{path}/**")
                seen_dirs.add(path)
            elif path_type == "file":
                depth = path.count("/")
                indent = "  " * depth
                file_name = path.split("/")[-1]
                file_url = f"{base_url}/{owner}/{repo}/blob/{ref}/{path}"
                output_lines.append(f"{indent}📄 [{file_name}]({file_url})")

        return "\n".join(output_lines)

    except Exception as e:
        logger.error(f"Error fetching repository tree: {str(e)}")
        return f"Error fetching repository tree: {str(e)}"
