"""Tools for retrieving file content from Gerrit projects."""

import json
import logging

from pydantic import BaseModel, Field

from ai_tools_gerrit.gerrit_client import GerritApiError, GerritClient, encode_project_name

logger = logging.getLogger(__name__)


class FileContentInput(BaseModel):
    """Input for retrieving file content from a Gerrit project branch."""

    project: str = Field(
        description="Gerrit project name (may include slashes, e.g. 'my/project').",
        examples=["my/project", "platform/tools"],
    )
    file_path: str = Field(
        description="Path to the file within the project.",
        examples=["README.md", "src/main.py"],
    )
    branch: str = Field(
        default="master",
        description="Branch to retrieve the file from.",
        examples=["master", "main"],
    )
    max_file_size: int = Field(
        default=50000,
        description="Maximum file size in characters (default: 50000).",
        examples=[10000, 50000],
    )


def get_file_content(
    project: str,
    file_path: str,
    gerrit: GerritClient,
    branch: str = "master",
    max_file_size: int = 50000,
) -> str:
    """Retrieve the content of a file from a Gerrit project branch.

    Fetches raw file content via the Gerrit REST API, decoding the
    base64-encoded response.  Binary files and files exceeding the size
    limit are rejected with descriptive error messages.

    Args:
        project: Gerrit project name (e.g. ``my/project``).
        file_path: Path to the file within the project.
        gerrit: Gerrit client instance.
        branch: Branch to retrieve the file from (default ``master``).
        max_file_size: Maximum file size in characters (default 50000).

    Returns:
        Raw file content as a string, or a descriptive error message.
    """
    encoded_project = encode_project_name(project)
    encoded_branch = encode_project_name(branch)
    encoded_file = encode_project_name(file_path)

    try:
        content_raw = gerrit.get_raw(
            f"/projects/{encoded_project}/branches/{encoded_branch}/files/{encoded_file}/content"
        )
    except GerritApiError as e:
        if e.status_code == 404:
            return f"Error: File '{file_path}' not found in project '{project}' on branch '{branch}'"
        if e.status_code == 403:
            return "Error: Access denied to project or file"
        if e.status_code == 401:
            return "Error: Authentication required"
        return f"Error fetching file content: {e}"

    logger.debug(
        "get_file_content: project=%s file=%s branch=%s raw_length=%d raw_preview=%r",
        project,
        file_path,
        branch,
        len(content_raw),
        content_raw[:120],
    )

    # Gerrit returns the content as a JSON-encoded string (quoted with escapes).
    # Parse the JSON string to get the actual file content.
    try:
        content = json.loads(content_raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning(
            "JSON decode failed for %s/%s (branch=%s): raw_length=%d raw_start=%r",
            project,
            file_path,
            branch,
            len(content_raw),
            content_raw[:200],
        )
        return f"Error: File '{file_path}' could not be decoded (unexpected response format from server)."

    if not isinstance(content, str):
        return f"Error: File '{file_path}' returned unexpected type from server."

    if len(content) > max_file_size:
        return f"Error: File too large ({len(content)} characters, limit: {max_file_size})"

    return content
