"""Tool for retrieving all issues from a repository with comprehensive timeline information."""

import re
from datetime import datetime
from typing import Any, cast

from loguru import logger
from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github

# Type alias for flexible key-value filters
IssueFilters = dict[str, Any]


class IssueTimeLineInput(BaseModel):
    """Input model for getting issue timeline."""

    owner: str = Field(
        description="The owner of the GitHub repository.",
        examples=["octocat", "microsoft", "tensorflow"],
    )
    repo: str = Field(
        description="The name of the GitHub repository.",
        examples=["Hello-World", "vscode", "tensorflow"],
    )
    limit: int = Field(
        default=100,
        description="Maximum number of issues to retrieve (default: 100, max: 1000).",
        examples=[50, 100, 500],
    )
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Key-value filters to apply. "
            "Common keys: status ('open', 'closed', 'all'), assignee, labels, milestone, author, mentioned. "
            "Example: {'status': 'open', 'assignee': 'username', 'labels': ['bug', 'urgent']}"
        ),
    )
    from_timestamp: str | None = Field(
        default=None,
        description=(
            "Optional ISO timestamp to filter timeline events from (inclusive). "
            "Events before this timestamp will be excluded."
        ),
        examples=["2025-11-18T20:18:55Z"],
    )
    to_timestamp: str | None = Field(
        default=None,
        description=(
            "Optional ISO timestamp to filter timeline events to (inclusive). "
            "Events after this timestamp will be excluded."
        ),
        examples=["2025-12-01T00:00:00Z"],
    )
    project_name: str | None = Field(
        default=None,
        description=(
            "Optional project name to filter issues. "
            "If provided, only issues that are attached to this specific project board will be analyzed. "
            "If not provided, all issues will be included."
        ),
        examples=["Development Board", "Sprint Planning"],
    )


def sanitize_author(username: str) -> str:
    """Sanitize author username to protect privacy."""
    return "Author"


def sanitize_markdown_authors(md_output: str) -> str:
    """
    Replace all user mentions in the text with 'Author'.
    Also replaces lines with 'Reviewed-by:' with an empty line.

    Args:
        md_output: The markdown output.

    Returns:
        The sanitized markdown output.
    """
    logger.info("Sanitizing author mentions in the markdown.")
    md_output = re.sub(
        r"^Reviewed-by:.*\r?\n?",
        "",
        md_output,
        flags=re.MULTILINE,
    ).strip()
    md_output = re.sub(r"@\w+", "@Author", md_output)
    return md_output


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime object."""
    if not timestamp_str or timestamp_str.strip() == "":
        raise ValueError(f"Invalid or empty timestamp string: '{timestamp_str}'")

    # Handle both with and without timezone info
    if timestamp_str.endswith("Z"):
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    return datetime.fromisoformat(timestamp_str)


def should_include_event(event_time: str, from_timestamp: str | None, to_timestamp: str | None = None) -> bool:
    """Check if event should be included based on timestamp filters.

    Args:
        event_time: The timestamp of the event
        from_timestamp: Optional start timestamp (inclusive). Events before this are excluded.
        to_timestamp: Optional end timestamp (inclusive). Events after this are excluded.

    Returns:
        True if the event should be included, False otherwise.
    """
    if not from_timestamp and not to_timestamp:
        return True

    # Skip events with empty or invalid timestamps
    if not event_time or event_time.strip() == "":
        return False

    try:
        event_dt = parse_timestamp(event_time)

        # Check from_timestamp (inclusive)
        if from_timestamp:
            filter_from_dt = parse_timestamp(from_timestamp)
            if event_dt < filter_from_dt:
                return False

        # Check to_timestamp (inclusive)
        if to_timestamp:
            filter_to_dt = parse_timestamp(to_timestamp)
            if event_dt > filter_to_dt:
                return False

        return True
    except ValueError as e:
        logger.warning(f"Skipping event with invalid timestamp '{event_time}': {e}")
        return False


def format_timeline_event(
    event: dict[str, Any],
    from_timestamp: str | None,
    to_timestamp: str | None,
    project_name: str | None,
) -> str | None:
    """Format a timeline event into a human-readable string.

    Args:
        event: Timeline event data
        from_timestamp: Optional start timestamp filter (inclusive)
        to_timestamp: Optional end timestamp filter (inclusive)
        project_name: Optional project name to filter project board events. If None, all projects are included.
    """
    event_type = event.get("__typename", "")
    created_at = event.get("createdAt", "")

    # Skip events with missing timestamps
    if not created_at or created_at.strip() == "":
        logger.warning(f"Skipping {event_type} event with missing createdAt timestamp")
        return None

    if not should_include_event(created_at, from_timestamp, to_timestamp):
        return None

    timestamp = created_at.replace("T", " ").replace("Z", "")

    if event_type == "IssueComment":
        body = event.get("body", "")[:100] + ("..." if len(event.get("body", "")) > 100 else "")
        return f"  {timestamp} - Comment added: {body}"

    elif event_type == "LabeledEvent":
        label = event.get("label", {}).get("name", "Unknown")
        return f"  {timestamp} - Label added: {label}"

    elif event_type == "UnlabeledEvent":
        label = event.get("label", {}).get("name", "Unknown")
        return f"  {timestamp} - Label removed: {label}"

    elif event_type == "ClosedEvent":
        return f"  {timestamp} - Status changed: OPEN → CLOSED"

    elif event_type == "ReopenedEvent":
        return f"  {timestamp} - Status changed: CLOSED → OPEN"

    elif event_type == "AssignedEvent":
        assignee = event.get("assignee", {}).get("login", "Unknown")
        sanitized_assignee = sanitize_author(assignee) if assignee != "Unknown" else assignee
        return f"  {timestamp} - Assigned to: {sanitized_assignee}"

    elif event_type == "UnassignedEvent":
        assignee = event.get("assignee", {}).get("login", "Unknown")
        sanitized_assignee = sanitize_author(assignee) if assignee != "Unknown" else assignee
        return f"  {timestamp} - Unassigned from: {sanitized_assignee}"

    elif event_type == "MilestonedEvent":
        milestone = event.get("milestoneTitle", "Unknown")
        return f"  {timestamp} - Milestone added: {milestone}"

    elif event_type == "DemilestonedEvent":
        milestone = event.get("milestoneTitle", "Unknown")
        return f"  {timestamp} - Milestone removed: {milestone}"

    elif event_type == "RenamedTitleEvent":
        previous = event.get("previousTitle", "Unknown")
        current = event.get("currentTitle", "Unknown")
        return f"  {timestamp} - Title changed from '{previous}' to '{current}'"

    elif event_type == "CrossReferencedEvent":
        source = event.get("source", {})
        source_type = source.get("__typename", "Unknown")
        if source_type == "PullRequest":
            pr_number = source.get("number", "Unknown")
            pr_title = source.get("title", "")[:50] + ("..." if len(source.get("title", "")) > 50 else "")
            return f"  {timestamp} - Referenced by PR #{pr_number}: {pr_title}"
        elif source_type == "Issue":
            issue_number = source.get("number", "Unknown")
            issue_title = source.get("title", "")[:50] + ("..." if len(source.get("title", "")) > 50 else "")
            return f"  {timestamp} - Referenced by Issue #{issue_number}: {issue_title}"

    elif event_type == "ReferencedEvent":
        commit = event.get("commit", {})
        commit_oid = commit.get("oid", "")[:8] if commit.get("oid") else "Unknown"
        commit_msg = commit.get("message", "")[:50] + ("..." if len(commit.get("message", "")) > 50 else "")
        return f"  {timestamp} - Referenced in commit {commit_oid}: {commit_msg}"

    elif event_type == "MovedColumnsInProjectEvent":
        event_project_name = event.get("project", {}).get("name", "Unknown Project")
        # Filter by project name if specified
        if project_name is not None and event_project_name.lower() != project_name.lower():
            return None
        previous_column = event.get("previousProjectColumnName", "Unknown")
        current_column = event.get("projectColumnName", "Unknown")
        return f"  {timestamp} - Project '{event_project_name}': Moved from '{previous_column}' to '{current_column}'"

    elif event_type == "AddedToProjectEvent":
        event_project_name = event.get("project", {}).get("name", "Unknown Project")
        # Filter by project name if specified
        if project_name is not None and event_project_name.lower() != project_name.lower():
            return None
        return f"  {timestamp} - Added to project: {event_project_name}"

    elif event_type == "RemovedFromProjectEvent":
        event_project_name = event.get("project", {}).get("name", "Unknown Project")
        # Filter by project name if specified
        if project_name is not None and event_project_name.lower() != project_name.lower():
            return None
        return f"  {timestamp} - Removed from project: {event_project_name}"

    # For any other event types, show a generic message
    return f"  {timestamp} - {event_type}"


def _build_issue_search_query(owner: str, repo: str, filters: IssueFilters) -> str:
    """
    Build a GitHub search query string from key-value filters.

    Args:
        owner: The repository owner
        repo: The repository name
        filters: Dictionary of filter key-value pairs

    Returns:
        A GitHub search query string
    """
    query_parts: list[str] = [
        "is:issue",
        f"repo:{owner}/{repo}",
    ]

    # Get filter values (case-insensitive key lookup)
    filter_lower = {k.lower(): v for k, v in filters.items()}

    # Add status filter
    status = filter_lower.get("status")
    if status:
        status_str = str(status).lower()
        if status_str == "open":
            query_parts.append("is:open")
        elif status_str == "closed":
            query_parts.append("is:closed")
        # "all" doesn't add any filter

    # Add assignee filter
    assignee = filter_lower.get("assignee")
    if assignee:
        if str(assignee).lower() == "none":
            query_parts.append("no:assignee")
        else:
            query_parts.append(f"assignee:{assignee}")

    # Add label filters
    labels = filter_lower.get("labels")
    if labels:
        if str(labels).lower() == "none":
            query_parts.append("no:label")
        elif isinstance(labels, list):
            for label in cast(list[str], labels):
                # Labels with spaces need to be quoted
                label_str = str(label)
                if " " in label_str:
                    query_parts.append(f'label:"{label_str}"')
                else:
                    query_parts.append(f"label:{label_str}")
        else:
            # Single label as string
            if " " in str(labels):
                query_parts.append(f'label:"{labels}"')
            else:
                query_parts.append(f"label:{labels}")

    # Add milestone filter
    milestone = filter_lower.get("milestone")
    if milestone:
        if str(milestone).lower() == "none":
            query_parts.append("no:milestone")
        elif " " in str(milestone):
            query_parts.append(f'milestone:"{milestone}"')
        else:
            query_parts.append(f"milestone:{milestone}")

    # Add author filter
    author = filter_lower.get("author")
    if author:
        query_parts.append(f"author:{author}")

    # Add mentioned filter
    mentioned = filter_lower.get("mentioned")
    if mentioned:
        query_parts.append(f"mentions:{mentioned}")

    return " ".join(query_parts)


def get_issue_time_line(
    owner: str,
    repo: str,
    github: Github,
    project_name: str | None = None,
    limit: int = 100,
    filters: IssueFilters | None = None,
    from_timestamp: str | None = None,
    to_timestamp: str | None = None,
) -> str:
    """Retrieve comprehensive timeline data for all issues in a repository.

    This function fetches detailed issue information including timeline events,
    labels, project board associations, and status changes. Useful for tracking
    issue history and understanding project progress over time.

    Args:
        owner: The owner of the GitHub repository.
        repo: The name of the GitHub repository.
        github: GitHub instance for API access.
        project_name: Optional project name to filter issues. If provided, only issues
            attached to this specific project board will be analyzed.
        limit: Maximum number of issues to retrieve (default: 100, max: 1000).
        filters: Optional dict of key-value filters to apply.
            Common keys: status ('open', 'closed', 'all'), assignee, labels, milestone, author, mentioned.
            Example: {'status': 'open', 'assignee': 'username', 'labels': ['bug']}
        from_timestamp: Optional ISO timestamp to filter timeline events from (inclusive).
        to_timestamp: Optional ISO timestamp to filter timeline events to (inclusive).

    Returns:
        Formatted markdown string with issue timeline data including issue details,
        labels, board status, and chronological timeline events.

    Raises:
        Exception: If the repository cannot be accessed or issues cannot be retrieved.
    """
    try:
        # Use empty dict if no filters provided
        if filters is None:
            filters = {}

        # Build the search query with filters
        search_query = _build_issue_search_query(owner, repo, filters)

        # Use GitHub's search API to find issues with filters
        search_result = github.query(
            f'search(type: ISSUE, first: {limit}, query: "{search_query}") {{'
            "issueCount "
            "nodes { "
            "... on Issue { "
            "title number url body createdAt state "
            "labels(last: 20) { nodes { name } } "
            "timelineItems(first: 100) { "
            "nodes { "
            "__typename "
            "... on IssueComment { createdAt body bodyHTML } "
            "... on LabeledEvent { createdAt label { name } } "
            "... on UnlabeledEvent { createdAt label { name } } "
            "... on ClosedEvent { createdAt } "
            "... on ReopenedEvent { createdAt } "
            "... on AssignedEvent { createdAt assignee { ... on User { login } ... on Bot { login } } } "
            "... on UnassignedEvent { createdAt assignee { ... on User { login } ... on Bot { login } } } "
            "... on MilestonedEvent { createdAt milestoneTitle } "
            "... on DemilestonedEvent { createdAt milestoneTitle } "
            "... on RenamedTitleEvent { createdAt previousTitle currentTitle } "
            "... on CrossReferencedEvent { createdAt source { __typename "
            "... on PullRequest { number title url } ... on Issue { number title url } } } "
            "... on ReferencedEvent { createdAt commit { oid message } } "
            "... on MovedColumnsInProjectEvent { createdAt project { name } "
            "previousProjectColumnName projectColumnName } "
            "... on AddedToProjectEvent { createdAt project { name } } "
            "... on RemovedFromProjectEvent { createdAt project { name } } "
            "} } "
            "projectItems(first: 10) { "
            "nodes { "
            "createdAt "
            "project { title url } "
            "fieldValues(first: 20) { "
            "nodes { "
            "__typename "
            "... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } } "
            "... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2Field { name } } } "
            "} } } } "
            "} } } }"
        )

        if "errors" in search_result:
            logger.error(f"GraphQL errors: {search_result['errors']}")
            return f"Error fetching issues: {search_result['errors']}"

        issues = search_result.get("search", {}).get("nodes", [])

        if not issues:
            return "No issues found in the repository."

        output_lines: list[str] = []

        for issue in issues:
            # Basic issue info
            issue_title = issue.get("title", "No Title")
            issue_url = issue.get("url", "")
            created_at = issue.get("createdAt", "").replace("T", " ").replace("Z", "")
            labels = [label["name"] for label in issue.get("labels", {}).get("nodes", [])]
            issue_state = issue.get("state", "UNKNOWN").upper()

            # Extract board status and priority from project field values
            board_status = "None"
            project_priority = None
            project_items = issue.get("projectItems", {}).get("nodes", [])
            for project_item in project_items:
                field_values = project_item.get("fieldValues", {}).get("nodes", [])
                for field_value in field_values:
                    field_name = ""
                    field_content = ""

                    if field_value.get("__typename") == "ProjectV2ItemFieldSingleSelectValue":
                        field_name = field_value.get("field", {}).get("name", "")
                        field_content = field_value.get("name", "")
                    elif field_value.get("__typename") == "ProjectV2ItemFieldTextValue":
                        field_name = field_value.get("field", {}).get("name", "")
                        field_content = field_value.get("text", "")

                    if field_name and field_content:
                        # Look for status/board status fields
                        if field_name.lower() in ["status", "board status", "state", "column"]:
                            board_status = field_content
                        # Look for priority fields
                        elif field_name.lower() in ["priority", "pri"] and not project_priority:
                            project_priority = field_content

            # Use project priority if found, otherwise use label-based priority
            if project_priority:
                priority = project_priority
            else:
                priority = "None"

            # Check if issue creation should be included based on timestamp filters
            if not should_include_event(issue.get("createdAt", ""), from_timestamp, to_timestamp):
                continue

            # If project_name is specified, only include issues that are attached to that project board
            if project_name is not None:
                project_items = issue.get("projectItems", {}).get("nodes", [])
                is_in_project = False

                for project_item in project_items:
                    project = project_item.get("project", {})
                    project_title = project.get("title", "")
                    if project_title.lower() == project_name.lower():
                        is_in_project = True
                        break

                # If the issue is not attached to the specified project, skip it entirely
                if not is_in_project:
                    continue

            # Format issue header with title, status, priority, and board status
            output_lines.append(f"# {issue_title}")
            output_lines.append(f"**URL:** {issue_url}")
            output_lines.append(
                f"**Status:** {issue_state} | **Board Status:** {board_status} | "
                f"**Priority:** {priority} | **Created:** {created_at}"
            )
            if labels:
                output_lines.append(f"**Labels:** {', '.join(labels)}")
            output_lines.append("")
            output_lines.append("## Timeline")
            output_lines.append("")

            # Add issue creation as first timeline event
            output_lines.append(f"  {created_at} - Issue created (status: OPEN)")

            # Process timeline items
            timeline_items = issue.get("timelineItems", {}).get("nodes", [])
            timeline_events: list[tuple[str, str]] = []

            for item in timeline_items:
                formatted_event = format_timeline_event(item, from_timestamp, to_timestamp, project_name)
                if formatted_event:
                    # Extract timestamp for sorting
                    created_at_item = item.get("createdAt", "")
                    timeline_events.append((created_at_item, formatted_event))

            # Sort timeline events by timestamp
            timeline_events.sort(key=lambda x: x[0])

            # Add sorted timeline events
            for _, event_str in timeline_events:
                output_lines.append(event_str)

            # Add project board information
            project_items = issue.get("projectItems", {}).get("nodes", [])
            for project_item in project_items:
                project_created = project_item.get("createdAt", "").replace("T", " ").replace("Z", "")
                if not should_include_event(project_item.get("createdAt", ""), from_timestamp, to_timestamp):
                    continue

                project = project_item.get("project", {})
                project_title = project.get("title", "Unknown Project")

                # Filter by project name if specified
                if project_name is not None and project_title.lower() != project_name.lower():
                    continue

                output_lines.append(f"  {project_created} - Added to project: {project_title}")

            output_lines.append("")  # Empty line between issues

        md_output = "\n".join(output_lines)
        # Apply comprehensive author sanitization to the final output
        md_output = sanitize_markdown_authors(md_output)
        return md_output

    except Exception as e:
        logger.error(f"Error fetching issues progress: {e}")
        return f"Error: {str(e)}"


def get_issue_time_line_from_input(**kwargs: Any) -> str:
    """Get comprehensive issues data with timeline events.

    Args:
        **kwargs: Arguments from IssueTimeLineInput including owner, repo, limit,
            filters, from_timestamp, to_timestamp, project_name

    Returns:
        Formatted markdown string with issues and timeline data
    """
    input_data = IssueTimeLineInput(**kwargs)
    github = Github()
    return get_issue_time_line(
        owner=input_data.owner,
        repo=input_data.repo,
        github=github,
        project_name=input_data.project_name,
        limit=input_data.limit,
        filters=input_data.filters,
        from_timestamp=input_data.from_timestamp,
        to_timestamp=input_data.to_timestamp,
    )
