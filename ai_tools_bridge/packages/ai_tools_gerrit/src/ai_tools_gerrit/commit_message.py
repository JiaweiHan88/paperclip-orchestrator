"""Tools for retrieving and analysing commit messages of Gerrit changes."""

import re
from typing import Any

from pydantic import BaseModel, Field

from ai_tools_gerrit.gerrit_client import GerritClient


def extract_bugs(commit_message: str) -> set[str]:
    """Extract bug IDs from a Gerrit commit message.

    Supports formats such as ``Bug: 12345``, ``Fixes: b/12345``,
    ``Closes: 12345, b/67890``, and inline mentions like ``b/12345``.

    Args:
        commit_message: Raw commit message text.

    Returns:
        Set of bug ID strings (numeric only, without the ``b/`` prefix).
    """
    bug_ids: set[str] = set()

    footer_pattern = r"^\s*(?:Bug|Fixes|Closes):\s*(.*)"
    for line in re.findall(footer_pattern, commit_message, re.MULTILINE | re.IGNORECASE):
        for pid in re.split(r"[\s,]+", line):
            if not pid:
                continue
            m = re.fullmatch(r"(?:b/)?(\d+)", pid)
            if m:
                bug_ids.add(m.group(1))

    for mid in re.findall(r"\bb/(\d+)\b", commit_message, re.IGNORECASE):
        bug_ids.add(mid)

    return bug_ids


class GetCommitMessageInput(BaseModel):
    """Input for retrieving the commit message of a Gerrit change."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )


def get_commit_message(change_id: str, gerrit: GerritClient) -> str:
    """Retrieve the commit message of the current patch set of a Gerrit change.

    Args:
        change_id: Change identifier.
        gerrit: Gerrit client instance.

    Returns:
        Formatted string with subject, full message, and footer fields.
    """
    commit_info: dict[str, Any] = gerrit.get(f"/changes/{change_id}/revisions/current/commit")

    output = f"Commit message for CL {change_id}:\n"
    output += f"Subject: {commit_info.get('subject', 'N/A')}\n\n"
    output += "Full Message:\n"
    output += "-" * 56 + "\n"
    output += f"{commit_info.get('message', 'Message not found.')}\n"
    output += "-" * 56 + "\n"

    footers: dict[str, Any] = commit_info.get("footers", {})
    if footers:
        output += "\nFooters:\n"
        for key, value in footers.items():
            output += f"- {key}: {value}\n"

    return output


class GetBugsFromClInput(BaseModel):
    """Input for extracting bug IDs from a Gerrit change's commit message."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )


def get_bugs_from_cl(change_id: str, gerrit: GerritClient) -> str:
    """Extract bug IDs referenced in the commit message of a Gerrit change.

    Args:
        change_id: Change identifier.
        gerrit: Gerrit client instance.

    Returns:
        Comma-separated list of bug IDs, or a message if none are found.
    """
    commit: dict[str, Any] = gerrit.get(f"/changes/{change_id}/revisions/current/commit")
    commit_message: str = commit.get("message", "")

    if not commit_message:
        return f"No commit message found for CL {change_id}."

    bug_ids = extract_bugs(commit_message)
    if not bug_ids:
        return f"No bug IDs found in the commit message for CL {change_id}."

    return f"Found bug(s) in CL {change_id}: {', '.join(sorted(bug_ids))}"
