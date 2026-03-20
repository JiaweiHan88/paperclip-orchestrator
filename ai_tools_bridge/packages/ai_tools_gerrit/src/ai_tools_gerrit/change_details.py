"""Tools for retrieving Gerrit change details."""

from typing import Any, cast

from pydantic import BaseModel, Field

from ai_tools_gerrit.gerrit_client import GerritClient


class GetChangeDetailsInput(BaseModel):
    """Input for retrieving comprehensive details of a Gerrit change."""

    change_id: str = Field(
        description=("Change identifier: numeric CL number, Change-Id string, or 'project~branch~Change-Id' triplet."),
        examples=["12345", "Ic1234567890abcdef", "my-project~main~Ic1234567890abcdef"],
    )
    options: list[str] | None = Field(
        default=None,
        description="Additional detail options (e.g. ['MESSAGES', 'ALL_REVISIONS']).",
        examples=[["MESSAGES"], ["ALL_REVISIONS", "DETAILED_LABELS"]],
    )


def get_change_details(
    change_id: str,
    gerrit: GerritClient,
    options: list[str] | None = None,
) -> str:
    """Retrieve a comprehensive summary of a Gerrit change.

    Fetches the full detail of a CL including owner, status, reviewers,
    votes, bugs in the commit message, and recent messages.

    Args:
        change_id: Change identifier (CL number, Change-Id, or triplet).
        gerrit: Gerrit client instance.
        options: Additional Gerrit detail options.

    Returns:
        Formatted string with CL details including subject, owner, status,
        reviewers with their votes, and recent review messages.
    """
    base_options = ["CURRENT_REVISION", "CURRENT_COMMIT", "DETAILED_LABELS"]
    if options:
        merged = list(set(base_options + options))
    else:
        merged = base_options

    params: dict[str, Any] = {"o": merged}
    details: dict[str, Any] = gerrit.get(f"/changes/{change_id}/detail", params=params)

    output = f"Summary for CL {details['_number']}:\n"
    output += f"Subject: {details['subject']}\n"
    output += f"Project: {details.get('project', 'N/A')}\n"
    output += f"Branch: {details.get('branch', 'N/A')}\n"
    output += f"Change-Id: {details.get('change_id', 'N/A')}\n"
    output += f"Owner: {details['owner'].get('email', details['owner'].get('name', 'N/A'))}\n"
    output += f"Status: {details['status']}\n"
    output += f"Created: {details.get('created', 'N/A')}\n"
    output += f"Updated: {details.get('updated', 'N/A')}\n"
    output += f"Changes: +{details.get('insertions', 0)} -{details.get('deletions', 0)}\n"

    if details.get("mergeable") is not None:
        output += f"Mergeable: {'Yes' if details['mergeable'] else 'No'}\n"
    if details.get("submittable") is not None:
        output += f"Submittable: {'Yes' if details['submittable'] else 'No'}\n"
    if details.get("topic"):
        output += f"Topic: {details['topic']}\n"

    # Extract bugs from commit message
    if "current_revision" in details:
        rev_info = details.get("revisions", {}).get(details["current_revision"], {})
        commit_msg = rev_info.get("commit", {}).get("message", "")
        if commit_msg:
            from ai_tools_gerrit.commit_message import extract_bugs

            bugs = extract_bugs(commit_msg)
            if bugs:
                output += f"Bugs: {', '.join(sorted(bugs))}\n"

    # Labels with approved/rejected summary
    labels_info: dict[str, Any] = details.get("labels", {})
    if labels_info:
        output += "Labels:\n"
        for label, info in labels_info.items():
            approved = info.get("approved")
            rejected = info.get("rejected")
            if approved:
                output += f"- {label}: Approved by {approved.get('name', 'Unknown')}\n"
            elif rejected:
                output += f"- {label}: Rejected by {rejected.get('name', 'Unknown')}\n"
            else:
                output += f"- {label}: Pending\n"
            # Show individual votes
            for vote in info.get("all", []):
                val = vote.get("value", 0)
                if val != 0:
                    vote_str = f"+{val}" if val > 0 else str(val)
                    voter = vote.get("name", vote.get("email", "Unknown"))
                    output += f"  - {voter}: {vote_str}\n"

    # Reviewers and their votes
    reviewers = details.get("reviewers", {}).get("REVIEWER", [])
    if reviewers:
        output += "Reviewers:\n"
        for reviewer in reviewers:
            votes: list[str] = []
            for label, info in labels_info.items():
                for vote in info.get("all", []):
                    if vote.get("_account_id") == reviewer.get("_account_id"):
                        val = vote.get("value", 0)
                        vote_str = f"+{val}" if val > 0 else str(val)
                        votes.append(f"{label}: {vote_str}")
            email = reviewer.get("email", "N/A")
            output += f"- {email} ({', '.join(votes)})\n"

    # Revisions (when ALL_REVISIONS data is present)
    revisions_raw: dict[str, Any] | None = details.get("revisions")
    if revisions_raw and len(revisions_raw) > 1:
        output += "Revisions:\n"
        sorted_revisions = sorted(revisions_raw.items(), key=lambda x: x[1].get("_number", 0))
        for rev_id, rev_data in sorted_revisions:
            ps_number = rev_data.get("_number", "?")
            kind = rev_data.get("kind", "")
            short_sha = rev_id[:8] if len(rev_id) > 8 else rev_id
            kind_str = f" - {kind}" if kind else ""
            output += f"- PS {ps_number} ({short_sha}){kind_str}\n"

    # Last 10 messages with truncation
    messages: list[dict[str, Any]] = details.get("messages", [])
    if messages:
        output += "Recent Messages:\n"
        for msg in messages[-10:]:
            author = msg.get("author", {}).get("name", "Gerrit")
            timestamp = msg.get("date", "No date")
            summary = msg["message"].splitlines()[0]
            if len(summary) > 200:
                summary = summary[:200] + "..."
            output += f"- (Patch Set {msg['_revision_number']}) [{timestamp}] ({author}): {summary}\n"

    return output


class ChangesSubmittedTogetherInput(BaseModel):
    """Input for listing changes that would be submitted together with a given CL."""

    change_id: str = Field(
        description="Change identifier (CL number, Change-Id, or triplet).",
        examples=["12345"],
    )
    options: list[str] | None = Field(
        default=None,
        description="Optional Gerrit query options.",
        examples=[["NON_VISIBLE_CHANGES"]],
    )


def changes_submitted_together(
    change_id: str,
    gerrit: GerritClient,
    options: list[str] | None = None,
) -> str:
    """List all changes that would be submitted together with a given CL.

    Queries Gerrit for the set of changes that share a topic or dependency chain
    and would be submitted as a unit.

    Args:
        change_id: Change identifier.
        gerrit: Gerrit client instance.
        options: Optional Gerrit query options.

    Returns:
        Formatted list of related changes, or a message if the change would be
        submitted by itself.
    """
    params: dict[str, Any] = {}
    if options:
        params["o"] = options

    data: Any = gerrit.get(f"/changes/{change_id}/submitted_together", params=params or None)

    changes: list[dict[str, Any]] = []
    non_visible: int = 0
    if isinstance(data, dict):
        data_dict = cast(dict[str, Any], data)
        changes = cast(list[dict[str, Any]], data_dict.get("changes", []))
        non_visible = int(data_dict.get("non_visible_changes", 0))
    elif isinstance(data, list):
        changes = cast(list[dict[str, Any]], data)

    if not changes:
        return "This change would be submitted by itself."

    output = f"The following {len(changes)} changes would be submitted together:\n"
    for change in changes:
        output += f"- {change['_number']}: {change['subject']}\n"
    if non_visible > 0:
        output += f"Plus {non_visible} other change(s) not visible to you.\n"
    return output
