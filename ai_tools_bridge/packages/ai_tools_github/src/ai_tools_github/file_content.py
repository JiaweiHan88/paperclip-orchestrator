"""Tool for retrieving individual file content from GitHub repositories."""

from loguru import logger
from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github


class FileContentInput(BaseModel):
    """Input model for getting the content of a specific file from a repository."""

    owner: str = Field(
        description="The owner of the GitHub repository.",
        examples=["octocat", "microsoft", "tensorflow"],
    )
    repo: str = Field(
        description="The name of the GitHub repository.",
        examples=["Hello-World", "vscode", "tensorflow"],
    )
    file_path: str = Field(
        description="The path to the file within the repository.",
        examples=[
            "README.md",
            "src/main.py",
            "docs/api.md",
            "config/settings.json",
        ],
    )
    ref: str = Field(
        default="HEAD",
        description="The git reference (branch, tag, or commit) to get the file from.",
        examples=["main", "HEAD", "v1.0.0", "feature-branch"],
    )
    max_file_size: int = Field(
        default=50000,
        description="Maximum file size in characters to process (default: 50000).",
        examples=[10000, 50000, 100000],
    )


def get_file_content(
    owner: str,
    repo: str,
    file_path: str,
    github: Github,
    ref: str = "HEAD",
    max_file_size: int = 50000,
) -> str:
    """
    Get the raw content of a specific file from a GitHub repository.

    This function retrieves the content of a single file from a GitHub repository,
    with intelligent validation for binary file types and file size limits. Only
    text files are supported to ensure meaningful content analysis. The tool
    automatically filters out binary files, lock files, and other non-processable
    files with clear error messages.

    This is particularly useful for code analysis, documentation review, and
    configuration inspection. The size limit prevents processing of extremely
    large files that could impact performance.

    Args:
        owner: The owner of the GitHub repository (username or organization)
        repo: The name of the GitHub repository
        file_path: Path to the file within the repository (e.g., 'src/main.py', 'docs/README.md')
        github: GitHub instance for API access
        ref: Git reference (branch, tag, or commit SHA) to get file from
        max_file_size: Maximum file size in characters to process (default: 50000)

    Returns:
        Raw content of the file as a string, or descriptive error message if file
        cannot be processed, not found, or access is denied

    Raises:
        Exception: If unexpected errors occur during file retrieval
    """
    try:
        # Get the file content using Github client
        content = github.get_file_content(owner, repo, ref, file_path)

        # Check file size limit
        if len(content) > max_file_size:
            logger.info(f"Skipping {file_path}: file too large ({len(content)} chars, limit: {max_file_size})")
            return f"Error: File too large ({len(content)} characters, limit: {max_file_size})"

        logger.info(f"Successfully retrieved {file_path} ({len(content)} characters)")
        return content

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error fetching file content: {error_msg}")

        # Handle common GitHub API errors
        if "404" in error_msg or "Not Found" in error_msg:
            return f"Error: File '{file_path}' not found in repository"
        elif "403" in error_msg or "Forbidden" in error_msg:
            return "Error: Access denied to repository or file"
        elif "401" in error_msg or "Unauthorized" in error_msg:
            return "Error: Authentication required"
        else:
            return f"Error fetching file content: {error_msg}"
