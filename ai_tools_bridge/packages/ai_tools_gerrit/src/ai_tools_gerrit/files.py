"""Tools for listing and diffing files in Gerrit changes."""

import json
from typing import Any, cast
from urllib.parse import quote

from pydantic import BaseModel, Field

from ai_tools_gerrit.gerrit_client import GerritApiError, GerritClient, encode_project_name


class ListChangeFilesInput(BaseModel):
    """Input for listing files modified in a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )


def list_change_files(change_id: str, gerrit: GerritClient) -> str:
    """List all files modified in the current patch set of a Gerrit change.

    Args:
        change_id: Change identifier.
        gerrit: Gerrit client instance.

    Returns:
        Formatted list of files with their status and line change counts.
    """
    files: dict[str, Any] = gerrit.get(f"/changes/{change_id}/revisions/current/files/")

    # Fetch patch set number for display
    detail: dict[str, Any] = gerrit.get(f"/changes/{change_id}/detail")
    patch_set = detail.get("current_revision_number", "current")

    output = f"Files in CL {change_id} (Patch Set {patch_set}):\n"
    total_inserted = 0
    total_deleted = 0
    file_count = 0

    for file_path, file_info in files.items():
        if file_path == "/COMMIT_MSG":
            continue
        status = file_info.get("status", "M")
        if status in ("A", "D", "R"):
            status_char = status
        else:
            status_char = "M"
        added = file_info.get("lines_inserted", 0)
        deleted = file_info.get("lines_deleted", 0)
        output += f"[{status_char}] {file_path} (+{added}, -{deleted})\n"

        if status_char == "R":
            old_path = file_info.get("old_path")
            if old_path:
                output += f"  (renamed from {old_path})\n"

        total_inserted += added
        total_deleted += deleted
        file_count += 1

    output += f"\nTotal: {file_count} files, +{total_inserted}, -{total_deleted}\n"
    return output


class GetFileDiffInput(BaseModel):
    """Input for retrieving the diff of a specific file in a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )
    file_path: str = Field(
        description="Path of the file within the repository.",
        examples=["src/main.py", "README.md"],
    )


def get_file_diff(change_id: str, file_path: str, gerrit: GerritClient) -> str:
    """Retrieve the diff for a specific file in the current patch set of a Gerrit change.

    The Gerrit API returns the patch as a JSON-encoded string; this function
    unwraps it and returns the plain-text diff.

    Args:
        change_id: Change identifier.
        file_path: Path of the file to diff.
        gerrit: Gerrit client instance.

    Returns:
        Decoded unified diff text for the specified file.
    """
    encoded_path = quote(file_path, safe="")
    # Gerrit returns the diff as a JSON-encoded string (XSSI prefix + quoted text)
    raw = gerrit.get_raw(f"/changes/{change_id}/revisions/current/patch?path={encoded_path}")
    # Parse the JSON string to get actual diff text
    content = raw.strip()
    if content.startswith('"') and content.endswith('"'):
        content = json.loads(content)
    return content


# ---------------------------------------------------------------------------
# Full-change diff (ported from ai_tools_gerrit2)
# ---------------------------------------------------------------------------


def _should_include_file(filename: str, file_scope: list[str] | None = None) -> bool:
    """Check if a filename should be included based on file_scope filter.

    Args:
        filename: The filename to check.
        file_scope: Optional list of file extensions or patterns to include.

    Returns:
        True if the file should be included.
    """
    if file_scope is None:
        return True
    if not file_scope:
        return False
    filename_lower = filename.lower()
    for scope_pattern in file_scope:
        if scope_pattern.startswith("."):
            if filename_lower.endswith(scope_pattern.lower()):
                return True
        elif scope_pattern.lower() in filename_lower:
            return True
    return False


class GetChangeDiffInput(BaseModel):
    """Input for retrieving diffs of all files in a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )
    revision_id: str = Field(
        default="current",
        description="Revision identifier ('current', number, or SHA).",
        examples=["current", "1"],
    )
    file_scope: list[str] | None = Field(
        default=None,
        description="Optional file extensions or patterns to include (e.g. ['.py', '.js']).",
        examples=[[".py", ".js"]],
    )


def get_change_diff(
    change_id: str,
    gerrit: GerritClient,
    revision_id: str = "current",
    file_scope: list[str] | None = None,
) -> str:
    """Retrieve diffs for all files in a Gerrit change revision.

    Lists all changed files in the revision and fetches per-file diffs
    via the Gerrit DiffInfo endpoint.  Optionally filters files by
    extension or pattern.

    Args:
        change_id: Change identifier (CL number, Change-Id, or triplet).
        gerrit: Gerrit client instance.
        revision_id: Revision identifier (default ``current``).
        file_scope: Optional list of file extensions or patterns to include.

    Returns:
        Formatted diff content showing file changes.
    """
    try:
        raw_files: Any = gerrit.get(f"/changes/{change_id}/revisions/{revision_id}/files")
    except GerritApiError as e:
        return f"Error fetching change diff: {e}"

    if not isinstance(raw_files, dict):
        return "No files found or unexpected response."

    files_dict = cast(dict[str, dict[str, Any]], raw_files)
    diff_lines: list[str] = []
    status_map: dict[str, str] = {"A": "added", "D": "deleted", "R": "renamed", "C": "copied", "M": "modified"}

    for filepath in sorted(files_dict):
        # Skip magic files unless explicitly in scope
        if filepath.startswith("/") and file_scope is None:
            continue
        if not _should_include_file(filepath, file_scope):
            continue

        file_info = files_dict[filepath]
        status: str = file_info.get("status", "M")
        lines_inserted: int = file_info.get("lines_inserted", 0)
        lines_deleted: int = file_info.get("lines_deleted", 0)
        status_text = status_map.get(status, "modified")

        if diff_lines:
            diff_lines.append("")

        try:
            file_diff: Any = gerrit.get(
                f"/changes/{change_id}/revisions/{revision_id}/files/{encode_project_name(filepath)}/diff"
            )

            if isinstance(file_diff, dict):
                typed_diff = cast(dict[str, Any], file_diff)
                diff_lines.append(f"--- a/{filepath}")
                diff_lines.append(f"+++ b/{filepath}")

                content: list[dict[str, Any]] = typed_diff.get("content", [])
                for section in content:
                    ab_lines: list[str] = section.get("ab", [])
                    a_lines: list[str] = section.get("a", [])
                    b_lines: list[str] = section.get("b", [])

                    if a_lines or b_lines:
                        for line in a_lines:
                            diff_lines.append(f"-{line}")
                        for line in b_lines:
                            diff_lines.append(f"+{line}")
                    elif ab_lines:
                        context_limit = 3
                        if len(ab_lines) <= context_limit * 2:
                            for line in ab_lines:
                                diff_lines.append(f" {line}")
                        else:
                            for line in ab_lines[:context_limit]:
                                diff_lines.append(f" {line}")
                            diff_lines.append(f"... ({len(ab_lines) - context_limit * 2} lines omitted) ...")
                            for line in ab_lines[-context_limit:]:
                                diff_lines.append(f" {line}")
            else:
                diff_lines.append(f"--- a/{filepath}")
                diff_lines.append(f"+++ b/{filepath}")
                diff_lines.append(f"File {status_text}: +{lines_inserted} -{lines_deleted}")

        except (GerritApiError, Exception):
            diff_lines.append(f"--- a/{filepath}")
            diff_lines.append(f"+++ b/{filepath}")
            diff_lines.append(f"File {status_text}: +{lines_inserted} -{lines_deleted}")

    if not diff_lines:
        scope_desc = f" (file scope: {file_scope})" if file_scope else ""
        return f"No relevant changes found{scope_desc}"

    return "\n".join(diff_lines)
