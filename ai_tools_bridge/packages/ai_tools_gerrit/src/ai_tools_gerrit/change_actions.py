"""Tools for performing actions on Gerrit changes."""

from typing import Any

from pydantic import BaseModel, Field

from ai_tools_gerrit.gerrit_client import GerritClient

# ---------------------------------------------------------------------------
# set_ready_for_review
# ---------------------------------------------------------------------------


class SetReadyForReviewInput(BaseModel):
    """Input for marking a Gerrit change as ready for review."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )


def set_ready_for_review(change_id: str, gerrit: GerritClient) -> str:
    """Mark a Gerrit change as ready for review (remove Work-In-Progress status).

    Args:
        change_id: Change identifier.
        gerrit: Gerrit client instance.

    Returns:
        Confirmation message.
    """
    gerrit.post(f"/changes/{change_id}/ready")
    return f"CL {change_id} is now ready for review."


# ---------------------------------------------------------------------------
# set_work_in_progress
# ---------------------------------------------------------------------------


class SetWorkInProgressInput(BaseModel):
    """Input for marking a Gerrit change as Work-In-Progress."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )
    message: str | None = Field(
        default=None,
        description="Optional message explaining why the CL is WIP.",
        examples=["Still resolving review comments."],
    )


def set_work_in_progress(change_id: str, gerrit: GerritClient, message: str | None = None) -> str:
    """Mark a Gerrit change as Work-In-Progress.

    Args:
        change_id: Change identifier.
        gerrit: Gerrit client instance.
        message: Optional message explaining the WIP status.

    Returns:
        Confirmation message.
    """
    payload: dict[str, Any] | None = {"message": message} if message else None
    gerrit.post(f"/changes/{change_id}/wip", payload=payload)
    return f"CL {change_id} is now marked as Work-In-Progress."


# ---------------------------------------------------------------------------
# set_topic
# ---------------------------------------------------------------------------


class SetTopicInput(BaseModel):
    """Input for setting or clearing the topic of a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )
    topic: str = Field(
        description="New topic string. Pass an empty string to delete the current topic.",
        examples=["feature/login-rework", ""],
    )


def set_topic(change_id: str, topic: str, gerrit: GerritClient) -> str:
    """Set or delete the topic of a Gerrit change.

    Args:
        change_id: Change identifier.
        topic: New topic. An empty string deletes the current topic.
        gerrit: Gerrit client instance.

    Returns:
        Confirmation message showing the new topic, or noting deletion.
    """
    result = gerrit.put(f"/changes/{change_id}/topic", payload={"topic": topic})
    if not result:
        return f"Topic deleted from CL {change_id}."
    return f"Topic for CL {change_id} set to: {result}"


# ---------------------------------------------------------------------------
# revert_change
# ---------------------------------------------------------------------------


class RevertChangeInput(BaseModel):
    """Input for reverting a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet) of the change to revert.",
        examples=["12345"],
    )
    message: str | None = Field(
        default=None,
        description="Optional custom commit message for the revert change.",
        examples=["Revert: unexpected regression in module X."],
    )


def revert_change(change_id: str, gerrit: GerritClient, message: str | None = None) -> str:
    """Revert a submitted Gerrit change, creating a new revert CL.

    Args:
        change_id: Change identifier of the change to revert.
        gerrit: Gerrit client instance.
        message: Optional commit message for the revert CL.

    Returns:
        Formatted string with the new revert CL number and subject.
    """
    payload: dict[str, Any] | None = {"message": message} if message else None
    revert_info: dict[str, Any] = gerrit.post(f"/changes/{change_id}/revert", payload=payload)

    if "_number" in revert_info:
        return (
            f"Successfully reverted CL {change_id}.\n"
            f"New revert CL: {revert_info['_number']}\n"
            f"Subject: {revert_info.get('subject', 'N/A')}"
        )
    return f"Revert request submitted for CL {change_id}."


# ---------------------------------------------------------------------------
# revert_submission
# ---------------------------------------------------------------------------


class RevertSubmissionInput(BaseModel):
    """Input for reverting an entire Gerrit submission."""

    change_id: str = Field(
        description="Change identifier of any CL in the submission to revert.",
        examples=["12345"],
    )
    message: str | None = Field(
        default=None,
        description="Optional commit message for the revert changes.",
        examples=["Revert submission due to CI failure."],
    )


def revert_submission(change_id: str, gerrit: GerritClient, message: str | None = None) -> str:
    """Revert an entire Gerrit submission, creating one or more revert CLs.

    Args:
        change_id: Change identifier of any CL in the submission.
        gerrit: Gerrit client instance.
        message: Optional commit message for the reverts.

    Returns:
        Formatted list of revert CLs created.
    """
    payload: dict[str, Any] | None = {"message": message} if message else None
    result: dict[str, Any] = gerrit.post(f"/changes/{change_id}/revert_submission", payload=payload)

    revert_changes: list[dict[str, Any]] = result.get("revert_changes", [])
    if revert_changes:
        output = f"Successfully reverted submission for CL {change_id}.\nCreated revert CLs:\n"
        for rc in revert_changes:
            output += f"- {rc['_number']}: {rc.get('subject', 'N/A')}\n"
        return output
    return f"Revert submission request submitted for CL {change_id}."


# ---------------------------------------------------------------------------
# create_change
# ---------------------------------------------------------------------------


class CreateChangeInput(BaseModel):
    """Input for creating a new Gerrit change."""

    project: str = Field(
        description="Repository name in Gerrit.",
        examples=["my-project"],
    )
    subject: str = Field(
        description="Commit message subject line.",
        examples=["feat: add support for dark mode"],
    )
    branch: str = Field(
        description="Target branch for the change.",
        examples=["main", "release/1.0"],
    )
    topic: str | None = Field(
        default=None,
        description="Optional topic to associate with the change.",
        examples=["feature/dark-mode"],
    )
    status: str | None = Field(
        default=None,
        description="Initial status of the change (e.g. 'DRAFT', 'NEW').",
        examples=["NEW", "DRAFT"],
    )


def create_change(
    project: str,
    subject: str,
    branch: str,
    gerrit: GerritClient,
    topic: str | None = None,
    status: str | None = None,
) -> str:
    """Create a new empty change in Gerrit.

    Args:
        project: Repository name in Gerrit.
        subject: Commit message subject line.
        branch: Target branch.
        gerrit: Gerrit client instance.
        topic: Optional topic.
        status: Optional initial status.

    Returns:
        Formatted string with the new CL number, subject, project and branch.
    """
    payload: dict[str, Any] = {
        "project": project,
        "subject": subject,
        "branch": branch,
    }
    if topic:
        payload["topic"] = topic
    if status:
        payload["status"] = status

    change_info: dict[str, Any] = gerrit.post("/changes/", payload=payload)

    if "_number" in change_info:
        return (
            f"Successfully created new change {change_info['_number']}.\n"
            f"Subject: {change_info.get('subject', subject)}\n"
            f"Project: {change_info.get('project', project)}, Branch: {change_info.get('branch', branch)}"
        )
    return f"Change creation request submitted for project '{project}'."


# ---------------------------------------------------------------------------
# abandon_change
# ---------------------------------------------------------------------------


class AbandonChangeInput(BaseModel):
    """Input for abandoning a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )
    message: str | None = Field(
        default=None,
        description="Optional message explaining why the change is abandoned.",
        examples=["Superseded by CL 12350."],
    )


def abandon_change(change_id: str, gerrit: GerritClient, message: str | None = None) -> str:
    """Abandon a Gerrit change.

    Args:
        change_id: Change identifier.
        gerrit: Gerrit client instance.
        message: Optional reason for abandonment.

    Returns:
        Confirmation message on success.
    """
    payload: dict[str, Any] | None = {"message": message} if message else None
    abandon_info: dict[str, Any] = gerrit.post(f"/changes/{change_id}/abandon", payload=payload)

    status = abandon_info.get("status", "")
    if status == "ABANDONED":
        return f"Successfully abandoned CL {change_id}."
    return f"CL {change_id} abandonment submitted (status: {status})."
