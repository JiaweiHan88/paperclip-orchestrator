"""JIRA field discovery and formatting functionality."""

import logging
from typing import Any, cast

from jira import JIRA
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GetJiraFieldsInput(BaseModel):
    """Input model for getting JIRA field definitions.

    Args:
        project_key: The project key (e.g., 'PROJ', 'SWH').
        issue_type: Optional issue type name (e.g., 'Story', 'Bug', 'Task').
        custom_fields_only: If True (default), returns only custom fields.
    """

    project_key: str = Field(
        description="The project key (e.g., 'PROJ', 'SWH').",
        examples=["SWH", "MCP", "PROJ"],
    )
    issue_type: str | None = Field(
        default=None,
        description="Optional issue type name. If not provided, returns all issue types and their fields.",
        examples=["Story", "Bug", "Task", "Epic"],
    )
    custom_fields_only: bool = Field(
        default=True,
        description="If True (default), returns only custom fields. If False, also include system fields.",
    )


def get_jira_fields(
    jira_instance: JIRA,
    project_key: str,
    issue_type: str | None = None,
    custom_fields_only: bool = True,
) -> str:
    """Get fields available for a project or specific issue type.

    Retrieves field metadata including IDs, names, types, required status,
    and allowed values. Useful for discovering available fields before
    creating or updating tickets.

    Args:
        jira_instance: JIRA instance to use for the operation.
        project_key: The project key (e.g., 'PROJ', 'SWH').
        issue_type: Optional issue type name.
                   If not provided, returns all issue types and their fields.
        custom_fields_only: If True (default), returns only custom fields.
                           If False, returns all fields including system fields.

    Returns:
        Markdown formatted string with field information including ID,
        type, required status, and allowed values.

    Raises:
        ValueError: If project or issue type not found.
    """
    field_label = "Custom Fields" if custom_fields_only else "Fields"
    result = f"# {field_label} for Project: {project_key}\n\n"

    # Get issue types for the project using the non-deprecated API
    issue_types = jira_instance.project_issue_types(project_key)

    if not issue_types:
        raise ValueError(f"No issue types found for project {project_key}")

    # Filter by issue type if specified
    if issue_type:
        issue_types = [it for it in issue_types if it.name.lower() == issue_type.lower()]
        if not issue_types:
            raise ValueError(f"Issue type '{issue_type}' not found in project {project_key}")

    for it in issue_types:
        issue_type_id = it.id
        issue_type_name = it.name

        result += f"## Issue Type: {issue_type_name}\n\n"

        # Get fields for this issue type using the non-deprecated API (requires issue type ID)
        fields = jira_instance.project_issue_fields(project_key, issue_type_id)

        if custom_fields_only:
            fields = [f for f in fields if f.fieldId.startswith("customfield_")]

        if not fields:
            result += f"_No {field_label.lower()} available_\n\n"
            continue

        for field in fields:
            field_id = field.fieldId
            field_name = field.name
            required = field.required
            schema = field.schema

            # Schema is a PropertyHolder object
            schema_type = schema.type if schema else "unknown"
            custom_type = getattr(schema, "custom", None) if schema else None

            type_text = schema_type
            if custom_type:
                custom_name = custom_type.split(":")[-1] if ":" in custom_type else custom_type
                type_text += f" ({custom_name})"

            result += f"- {field_name} ({field_id}, {'required' if required else 'optional'}): {type_text}\n"

            # Show allowed values if available
            allowed_values: list[Any] = field.allowedValues if hasattr(field, "allowedValues") else []
            if allowed_values and len(allowed_values) <= 10:
                values: list[Any] = [v.name if hasattr(v, "name") else v.value for v in allowed_values if v]
                result += f"  Allowed Values: {', '.join(str(v) for v in values if v)}\n"
            elif allowed_values:
                result += f"  Allowed Values: {len(allowed_values)} options available\n"

    return result


def build_field_map(jira_instance: JIRA) -> dict[str, str]:
    """Build a mapping of field names to field IDs.

    Args:
        jira_instance: JIRA instance to use for the operation.

    Returns:
        Dictionary mapping lowercase field names to field IDs.
    """
    fields: list[dict[str, Any]] = jira_instance.fields()  # pyright: ignore

    field_map: dict[str, str] = {}

    for field in fields:
        field_id = field.get("id", "")
        field_name = field.get("name", "")

        if field_id and field_name:
            # Map lowercase name to ID
            field_map[field_name.lower()] = field_id
            # Also map ID to itself for direct lookups
            field_map[field_id] = field_id

    # Add special mappings for known checklist fields
    if "definition of done" not in field_map:
        field_map["definition of done"] = "customfield_10400"
    if "acceptance criteria" not in field_map:
        field_map["acceptance criteria"] = "customfield_10200"

    return field_map


def format_field_value(field_name: str, value: Any, jira_instance: JIRA) -> Any:
    """Format a field value based on its type for JIRA API.

    Args:
        field_name: The field name or ID.
        value: The value to format.
        jira_instance: JIRA instance to get field metadata.

    Returns:
        Properly formatted value for JIRA API.
    """
    # Get field definition
    fields: list[dict[str, Any]] = jira_instance.fields()  # pyright: ignore
    field_def: dict[str, Any] | None = None

    # Find field definition by ID or name
    for field in fields:
        if field.get("id") == field_name or field.get("name", "").lower() == field_name.lower():
            field_def = field
            break

    if not field_def:
        logger.warning(f"Field definition not found for: {field_name}, using value as-is")
        return value

    field_name_lower = field_def.get("name", "").lower()
    field_id = field_def.get("id", "")
    schema: dict[str, Any] = field_def.get("schema", {})
    schema_type = schema.get("type", "")

    # Special handling for checklist fields (Definition of Done, Acceptance Criteria)
    # These fields require format: [{"name": item, "checked": False, "mandatory": True}]
    if field_name_lower in ["definition of done", "acceptance criteria"] or field_id in [
        "customfield_10400",
        "customfield_10200",
    ]:
        if isinstance(value, list):
            formatted_checklist: list[dict[str, Any]] = []
            for item in cast(list[Any], value):
                if isinstance(item, str):
                    # Convert string to checklist item format
                    formatted_checklist.append(
                        cast(dict[str, Any], {"name": item, "checked": False, "mandatory": True})
                    )  # pyright: ignore[reportUnknownMemberType]
                elif isinstance(item, dict):
                    # Already formatted, use as-is
                    formatted_checklist.append(item)  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
                else:
                    logger.warning(f"Invalid checklist item: {item}")
            checklist_result: list[Any] = formatted_checklist
            return checklist_result  # pyright: ignore[reportUnknownVariableType]
        else:
            logger.warning(f"Checklist field {field_name} requires list value, got: {type(value)}")
            return None

    # Format based on field name and type
    if field_name_lower == "priority":
        if isinstance(value, str):
            return cast(dict[str, Any], {"name": value})
        elif isinstance(value, dict):
            return cast(dict[str, Any], value)
        else:
            logger.warning(f"Invalid priority value: {value}")
            return None

    elif field_name_lower == "assignee" or field_name_lower == "reporter":
        if value is None or value == "":
            return None
        elif isinstance(value, str):
            return cast(dict[str, Any], {"name": value})
        elif isinstance(value, dict):
            return cast(dict[str, Any], value)
        else:
            logger.warning(f"Invalid {field_name_lower} value: {value}")
            return None

    elif field_name_lower == "labels":
        if isinstance(value, list):
            return cast(list[Any], value)
        elif isinstance(value, str):
            return [label.strip() for label in value.split(",") if label.strip()]
        else:
            logger.warning(f"Invalid labels value: {value}")
            return None

    elif field_name_lower in ["components", "fixversions", "versions"]:
        if isinstance(value, list):
            formatted_list: list[dict[str, Any]] = []
            for item in cast(list[Any], value):
                if isinstance(item, str):
                    formatted_list.append(cast(dict[str, Any], {"name": item}))
                elif isinstance(item, dict):
                    formatted_list.append(item)  # pyright: ignore[reportUnknownArgumentType]
                else:
                    logger.warning(f"Invalid item in {field_name_lower}: {item}")
            return formatted_list
        else:
            logger.warning(f"Invalid {field_name_lower} value: {value}")
            return None

    elif schema_type == "array" and isinstance(value, list):
        # Handle array types - check if items should be objects
        items_type = schema.get("items", "")
        if isinstance(items_type, str) and items_type in ["option", "component", "version"]:
            # Format as list of objects with name
            return [
                cast(dict[str, Any], {"name": item}) if isinstance(item, str) else item
                for item in cast(list[Any], value)
            ]
        return cast(list[Any], value)

    elif schema_type == "option":
        # Single select field
        if isinstance(value, str):
            return cast(dict[str, Any], {"value": value})
        elif isinstance(value, dict):
            return cast(dict[str, Any], value)
        else:
            logger.warning(f"Invalid option value for {field_name}: {value}")
            return None

    elif schema_type == "user":
        # User field
        if value is None or value == "":
            return None
        elif isinstance(value, str):
            return cast(dict[str, Any], {"name": value})
        elif isinstance(value, dict):
            return cast(dict[str, Any], value)
        else:
            logger.warning(f"Invalid user value: {value}")
            return None

    # Default: return value as-is
    return value


def resolve_field_updates(
    updates: dict[str, Any],
    jira_instance: JIRA,
) -> dict[str, Any]:
    """Resolve field names to IDs and format values appropriately.

    Args:
        updates: Dictionary of field names/IDs to values.
        jira_instance: JIRA instance to use for field resolution.

    Returns:
        Dictionary with field IDs and properly formatted values.
    """
    field_map = build_field_map(jira_instance)
    resolved_updates: dict[str, Any] = {}

    for key, value in updates.items():
        # Skip None values
        if value is None:
            continue

        # Resolve field name to ID
        field_id = field_map.get(key.lower(), key)

        # Format the value
        formatted_value = format_field_value(field_id, value, jira_instance)

        if formatted_value is not None:
            resolved_updates[field_id] = formatted_value
        else:
            logger.warning(f"Skipping field {key} due to formatting error")

    return resolved_updates
