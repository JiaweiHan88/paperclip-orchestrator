"""Tools for setting review labels and votes on Gerrit changes."""

from typing import Any

from pydantic import BaseModel, Field

from ai_tools_gerrit.gerrit_client import GerritClient


class SetReviewInput(BaseModel):
    """Input for setting review labels/votes on a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )
    revision_id: str = Field(
        default="current",
        description="Revision (patchset) to review. Use 'current' for the latest.",
        examples=["current", "1", "2"],
    )
    labels: dict[str, int] | None = Field(
        default=None,
        description="Label names to vote values (e.g. {'Code-Review': 2, 'Verified': 1}).",
        examples=[{"Code-Review": 1}, {"Code-Review": 2, "Verified": 1}],
    )
    message: str | None = Field(
        default=None,
        description="Optional review message to include.",
        examples=["LGTM!"],
    )


def set_review(
    change_id: str,
    gerrit: GerritClient,
    revision_id: str = "current",
    labels: dict[str, int] | None = None,
    message: str | None = None,
) -> str:
    """Set review labels and/or post a review message on a Gerrit change.

    Submits a review on a specific revision of a change, optionally
    setting label votes and including a review message.  This is distinct
    from ``post_review_comment`` which posts inline comments on specific
    file lines.

    Args:
        change_id: Change identifier (CL number, Change-Id, or triplet).
        gerrit: Gerrit client instance.
        revision_id: Revision to review (default ``current``).
        labels: Optional dict of label names to vote values.
        message: Optional review message.

    Returns:
        Confirmation message or error description.
    """
    review_input: dict[str, Any] = {}
    if labels:
        review_input["labels"] = labels
    if message:
        review_input["message"] = message

    if not review_input:
        return "Error: At least one of 'labels' or 'message' must be provided."

    gerrit.post(f"/changes/{change_id}/revisions/{revision_id}/review", payload=review_input)

    parts: list[str] = []
    if labels:
        label_strs = [f"{name}: {'+' if val > 0 else ''}{val}" for name, val in labels.items()]
        parts.append(f"Labels set: {', '.join(label_strs)}")
    if message:
        parts.append("Review message posted")

    return f"Successfully reviewed CL {change_id}: {'; '.join(parts)}"
