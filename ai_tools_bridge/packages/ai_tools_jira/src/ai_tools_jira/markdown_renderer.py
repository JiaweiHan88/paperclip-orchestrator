"""JIRA issue markdown rendering functionality."""

import logging
from typing import Any, cast

from jira import JIRA
from jira.resources import Attachment, Comment, Issue

from .fields import build_field_map

logger = logging.getLogger(__name__)


def convert_checkbox_list_to_text(title: str, items: list[Any]) -> str:
    """Convert a checkbox list to a markdown text.

    Args:
        title: The title of the list.
        items: The list of items.

    Returns:
        The markdown text representation of the checkbox list.
    """
    # Handle case where items is a string (some Jira instances return strings for custom fields)
    if isinstance(items, str):
        return f"\n\n## {title}\n{items}\n"

    text = f"\n\n## {title}\n"
    for item in items:
        # Check if item has the expected attributes (checkbox list format)
        if not hasattr(item, "isHeader"):
            # If item doesn't have expected structure, just convert to string
            text += f"- {item}\n"
            continue

        if item.isHeader:
            text += f"\n{item.name}\n"
        else:
            check_mark = "x" if item.checked else " "
            required = " (required)" if item.mandatory else ""
            text += f"- [{check_mark}] {item.name}{required}\n"

    return text


# Default fields that are always included in the output
DEFAULT_FIELDS = [
    "summary",
    "status",
    "assignee",
    "reporter",
    "priority",
    "components",
    "created",
    "updated",
    "description",
    "attachment",
    "comment",
]


def format_field_for_display(field_name: str, field_value: Any) -> str | None:
    """Format a field value for display in markdown.

    Args:
        field_name: The name or ID of the field.
        field_value: The value of the field.

    Returns:
        Formatted string for display, or None if the field should be skipped.
    """
    if field_value is None:
        return None

    # Handle different field value types
    if isinstance(field_value, str):
        return field_value
    elif isinstance(field_value, (int, float, bool)):
        return str(field_value)
    elif isinstance(field_value, list):
        # Handle list of objects (e.g., components, labels)
        if not field_value:
            return None
        field_list = cast(list[Any], field_value)
        if all(isinstance(item, str) for item in field_list):
            return ", ".join(cast(list[str], field_list))
        elif all(hasattr(item, "name") for item in field_list):
            return ", ".join(item.name for item in field_list)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        else:
            return str(field_list)
    elif hasattr(field_value, "name"):
        # Handle objects with name attribute (e.g., status, priority)
        return field_value.name
    elif hasattr(field_value, "displayName"):
        # Handle user objects
        return field_value.displayName
    else:
        # For complex objects, convert to string
        return str(field_value)


# Fields that are already displayed in default sections
_ALREADY_DISPLAYED_FIELDS = {
    "summary",
    "status",
    "assignee",
    "reporter",
    "priority",
    "components",
    "created",
    "updated",
    "description",
    "attachment",
    "comment",
    "key",
    "issuetype",
    "project",
}


def _render_basic_details(issue: Issue) -> str:
    """Render basic issue details section.

    Args:
        issue: The JIRA issue object with fields attribute.

    Returns:
        Markdown string with basic issue details.
    """
    output = f"**Key:** {issue.key}\n"

    status = getattr(issue.fields, "status", None)
    if status and getattr(status, "name", None):
        output += f"**Status:** {status.name}\n"

    assignee = getattr(issue.fields, "assignee", None)
    if assignee and getattr(assignee, "displayName", None):
        output += f"**Assignee:** {assignee.displayName}\n"

    reporter = getattr(issue.fields, "reporter", None)
    if reporter and getattr(reporter, "displayName", None):
        output += f"**Reporter:** {reporter.displayName}\n"

    priority = getattr(issue.fields, "priority", None)
    if priority and getattr(priority, "name", None):
        output += f"**Priority:** {priority.name}\n"

    components = getattr(issue.fields, "components", None)
    if isinstance(components, list) and components:
        component_names = ", ".join([comp.name for comp in components])  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportUnknownVariableType]
        output += f"**Components:** {component_names}\n"

    created = getattr(issue.fields, "created", None)
    if created:
        output += f"**Created:** {created}\n"

    updated = getattr(issue.fields, "updated", None)
    if updated:
        output += f"**Updated:** {updated}\n"

    return output


def _render_attachments(attachments: list[Attachment]) -> str:
    """Render attachments section.

    Args:
        attachments: List of attachment objects.

    Returns:
        Markdown string with attachments section, or empty string if no attachments.
    """
    if not attachments:
        return ""

    output = "## Attachments\n\n"
    for attachment in attachments:
        attachment_id = attachment.id
        attachment_name = attachment.filename
        output += f"- {attachment_id}: {attachment_name}\n"
    output += "\n"

    return output


def _render_comments(comments: list[Comment]) -> str:
    """Render comments section.

    Args:
        comments: List of comment objects.

    Returns:
        Markdown string with comments section, or empty string if no comments.
    """
    if not comments:
        return ""

    output = "## Comments\n\n"
    for comment in comments:
        author = comment.author.displayName
        created = comment.created
        body = comment.body
        output += f"**{author}** ({created}):\n{body}\n\n"

    return output


def _build_field_maps(jira_instance: JIRA) -> tuple[dict[str, str], dict[str, str]]:
    """Build field name to ID and ID to name mappings.

    Args:
        jira_instance: JIRA instance for field discovery.

    Returns:
        Tuple of (field_map, reverse_field_map) where:
        - field_map: Maps lowercase field names to field IDs
        - reverse_field_map: Maps field IDs to display names
    """
    field_map = build_field_map(jira_instance)
    reverse_field_map: dict[str, str] = {}

    # Build reverse map (field ID to field name)
    all_fields = jira_instance.fields()  # pyright: ignore
    for field in all_fields:
        field_id = field.get("id", "")
        field_name = field.get("name", "")
        if field_id and field_name:
            reverse_field_map[field_id] = field_name

    return field_map, reverse_field_map


def _determine_fields_to_include(
    issue: Issue,
    fields: list[str] | None,
    field_map: dict[str, str],
) -> set[str]:
    """Determine which fields should be included in the output.

    Args:
        issue: The JIRA issue object.
        fields: Optional list of field names or IDs.
                None = no additional fields,
                [] (empty list) = all fields,
                ['field1', ...] = specific additional fields.
        field_map: Map of lowercase field names to field IDs.

    Returns:
        Set of field IDs to include.
    """
    fields_to_include: set[str] = set()

    if fields is not None and len(fields) == 0:
        # Empty list means include all fields
        fields_to_include = {name for name in dir(issue.fields) if not name.startswith("_")}
    elif fields:
        # Specific fields requested - resolve field names to IDs using field_map
        for field in fields:
            field_id = field_map.get(field.lower(), field)
            fields_to_include.add(field_id)

    return fields_to_include


def _render_additional_fields(
    issue: Issue,
    fields_to_include: set[str],
    reverse_field_map: dict[str, str],
) -> str:
    """Render additional fields section.

    Args:
        issue: The JIRA issue object.
        fields_to_include: Set of field IDs to include.
        reverse_field_map: Map of field IDs to display names.

    Returns:
        Markdown string with additional fields section, or empty string if no fields.
    """
    additional_field_outputs: list[tuple[str, str]] = []

    for field_id in fields_to_include:
        if field_id in _ALREADY_DISPLAYED_FIELDS:
            continue

        # Get field value from issue
        field_value = getattr(issue.fields, field_id, None)

        if field_value is None:
            continue

        # Format the field for display
        formatted_value = format_field_for_display(field_id, field_value)

        if formatted_value:
            # Get human-readable field name
            field_display_name = reverse_field_map.get(field_id, field_id)
            additional_field_outputs.append((field_display_name, formatted_value))

    # Add additional fields section if there are any
    if not additional_field_outputs:
        return ""

    output = "## Additional Fields\n\n"
    for field_name, field_value in sorted(additional_field_outputs):
        output += f"**{field_name}**: {field_value}\n"
    output += "\n"

    return output


def render_issue_to_markdown(
    issue: Issue,
    jira_instance: JIRA | None = None,
    fields: list[str] | None = None,
) -> str:
    """Render a JIRA issue to markdown format.

    Args:
        issue: The JIRA issue object with fields attribute.
        jira_instance: Optional JIRA instance for field name resolution.
        fields: Optional list of field names or IDs to include.
                None (default) = standard fields only,
                [] (empty list) = all available fields,
                ['field1', ...] = standard fields + specified fields.

    Returns:
        Formatted markdown string representation of the issue.
    """
    # Extract basic issue information
    title = issue.fields.summary
    description = issue.fields.description or "No description provided"
    comments = issue.fields.comment.comments
    attachments = issue.fields.attachment

    # Start building markdown output
    markdown_output = f"# {title}\n\n"

    # Add basic issue details
    markdown_output += _render_basic_details(issue)
    markdown_output += "\n"

    # Add description
    markdown_output += f"## Description\n{description}\n\n"

    # Add attachments section
    markdown_output += _render_attachments(attachments)

    # Add comments section
    markdown_output += _render_comments(comments)

    # Add additional fields if requested
    if fields is not None:
        # Build field maps if jira_instance is provided
        field_map: dict[str, str] = {}
        reverse_field_map: dict[str, str] = {}

        if jira_instance:
            field_map, reverse_field_map = _build_field_maps(jira_instance)

        # Determine which fields to include
        fields_to_include = _determine_fields_to_include(issue, fields, field_map)

        # Render additional fields section
        markdown_output += _render_additional_fields(issue, fields_to_include, reverse_field_map)

    return markdown_output
