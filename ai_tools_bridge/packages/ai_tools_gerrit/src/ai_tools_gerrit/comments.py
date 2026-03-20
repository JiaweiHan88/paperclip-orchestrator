"""Tools for listing and posting comments on Gerrit changes."""

from typing import Any

from pydantic import BaseModel, Field

from ai_tools_gerrit.gerrit_client import GerritClient


class ListChangeCommentsInput(BaseModel):
    """Input for listing comments on a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )


def list_change_comments(change_id: str, gerrit: GerritClient) -> str:
    """List all published comments on a Gerrit change, grouped by file.

    Retrieves resolved and unresolved inline comments from all reviewers.

    Args:
        change_id: Change identifier.
        gerrit: Gerrit client instance.

    Returns:
        Formatted string with comments grouped by file, showing author, timestamp,
        resolution status, and comment text.
    """
    comments_by_file: dict[str, list[dict[str, Any]]] = gerrit.get(f"/changes/{change_id}/comments")

    if not comments_by_file:
        return f"No comments found for CL {change_id}."

    output = f"Comments for CL {change_id}:\n"
    for file_path, comments in comments_by_file.items():
        output += f"---\nFile: {file_path}\n"
        for comment in comments:
            line = comment.get("line", "File")
            author = comment.get("author", {}).get("name", "Unknown")
            timestamp = comment.get("updated", "No date")
            message = comment.get("message", "")
            status = "UNRESOLVED" if comment.get("unresolved", False) else "RESOLVED"
            output += f"L{line}: [{author}] ({timestamp}) - {status}\n"
            output += f"  {message}\n"

    return output


class PostReviewCommentInput(BaseModel):
    """Input for posting an inline review comment on a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )
    file_path: str = Field(
        description="Path of the file to comment on.",
        examples=["src/main.py"],
    )
    line_number: int = Field(
        description="Line number to attach the comment to.",
        examples=[42],
    )
    message: str = Field(
        description="Comment text.",
        examples=["This should be refactored to avoid duplicating logic."],
    )
    unresolved: bool = Field(
        default=True,
        description="Whether the comment is unresolved (requires author action). Defaults to True.",
    )
    labels: dict[str, int] | None = Field(
        default=None,
        description="Vote labels to set simultaneously (e.g. {'Code-Review': -1}).",
        examples=[{"Code-Review": -1}],
    )


def post_review_comment(
    change_id: str,
    file_path: str,
    line_number: int,
    message: str,
    gerrit: GerritClient,
    unresolved: bool = True,
    labels: dict[str, int] | None = None,
) -> str:
    """Post an inline review comment on a specific line of a file in a Gerrit change.

    Optionally sets vote labels at the same time.

    Args:
        change_id: Change identifier.
        file_path: File path to attach the comment to.
        line_number: Line number within the file.
        message: Comment text.
        gerrit: Gerrit client instance.
        unresolved: Whether the comment is unresolved.
        labels: Optional vote labels to set.

    Returns:
        Confirmation message on success.
    """
    payload: dict[str, Any] = {
        "comments": {
            file_path: [
                {
                    "line": line_number,
                    "message": message,
                    "unresolved": unresolved,
                }
            ]
        },
    }
    if labels:
        payload["labels"] = labels

    gerrit.post(f"/changes/{change_id}/revisions/current/review", payload=payload)
    return f"Successfully posted comment on CL {change_id}, file '{file_path}' at line {line_number}."
