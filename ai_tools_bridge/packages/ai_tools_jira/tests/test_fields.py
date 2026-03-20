"""Tests for JIRA fields functionality.

This module contains comprehensive tests for field discovery, field mapping,
and field value formatting.
"""

import unittest
from unittest.mock import Mock

from ai_tools_jira.fields import (
    GetJiraFieldsInput,
    build_field_map,
    format_field_value,
    get_jira_fields,
    resolve_field_updates,
)


class TestGetJiraFieldsInput(unittest.TestCase):
    """Test cases for the GetJiraFieldsInput Pydantic model.

    Tests validation of input parameters and model behavior.
    """

    def test_valid_input_minimal(self):
        """Test that model accepts minimal valid input with project_key."""
        input_data = GetJiraFieldsInput(project_key="SWH")
        self.assertEqual(input_data.project_key, "SWH")
        self.assertIsNone(input_data.issue_type)
        self.assertTrue(input_data.custom_fields_only)

    def test_valid_input_with_issue_type(self):
        """Test that model accepts valid input with issue type."""
        input_data = GetJiraFieldsInput(project_key="SWH", issue_type="Story")
        self.assertEqual(input_data.project_key, "SWH")
        self.assertEqual(input_data.issue_type, "Story")
        self.assertTrue(input_data.custom_fields_only)

    def test_valid_input_all_fields(self):
        """Test that model accepts custom_fields_only=False flag."""
        input_data = GetJiraFieldsInput(project_key="SWH", custom_fields_only=False)
        self.assertEqual(input_data.project_key, "SWH")
        self.assertFalse(input_data.custom_fields_only)


class TestGetJiraFields(unittest.TestCase):
    """Test cases for the get_jira_fields function.

    Tests successful retrieval and formatting of field definitions.
    """

    def setUp(self):
        """Set up test fixtures and common test data."""
        self.mock_jira = Mock()

        # Mock issue type data
        mock_issue_type = Mock()
        mock_issue_type.id = "10001"
        mock_issue_type.name = "Story"
        self.mock_issue_types = [mock_issue_type]

        # Mock field data with PropertyHolder-like schema
        def create_mock_field(field_id, name, required, schema_type, custom_type=None):
            field = Mock()
            field.fieldId = field_id
            field.name = name
            field.required = required
            field.schema = Mock()
            field.schema.type = schema_type
            if custom_type:
                field.schema.custom = custom_type
            else:
                # Simulate missing custom attribute for system fields
                del field.schema.custom
            field.allowedValues = []
            return field

        self.mock_fields = [
            create_mock_field("summary", "Summary", True, "string"),
            create_mock_field("priority", "Priority", False, "priority"),
            create_mock_field("customfield_10400", "Definition of Done", False, "array", "com.example:checklist"),
            create_mock_field("customfield_10200", "Acceptance Criteria", False, "array", "com.example:checklist"),
        ]

    def test_get_all_fields(self):
        """Test retrieving all fields for a project."""
        self.mock_jira.project_issue_types.return_value = self.mock_issue_types
        self.mock_jira.project_issue_fields.return_value = self.mock_fields

        result = get_jira_fields(jira_instance=self.mock_jira, project_key="SWH", custom_fields_only=False)

        # Verify project_issue_types was called
        self.mock_jira.project_issue_types.assert_called_once_with("SWH")

        # Verify result contains all fields
        self.assertIn("Summary", result)
        self.assertIn("Priority", result)
        self.assertIn("Definition of Done", result)
        self.assertIn("Acceptance Criteria", result)

    def test_get_custom_fields_only(self):
        """Test retrieving only custom fields."""
        self.mock_jira.project_issue_types.return_value = self.mock_issue_types
        self.mock_jira.project_issue_fields.return_value = self.mock_fields

        result = get_jira_fields(jira_instance=self.mock_jira, project_key="SWH", custom_fields_only=True)

        # Verify result contains only custom fields
        self.assertIn("Definition of Done", result)
        self.assertIn("Acceptance Criteria", result)
        self.assertNotIn("Summary", result)
        self.assertNotIn("Priority", result)

    def test_get_fields_by_issue_type(self):
        """Test retrieving fields for specific issue type."""
        self.mock_jira.project_issue_types.return_value = self.mock_issue_types
        self.mock_jira.project_issue_fields.return_value = self.mock_fields

        result = get_jira_fields(jira_instance=self.mock_jira, project_key="SWH", issue_type="Story")

        # Verify project_issue_fields was called with correct issue type ID
        self.mock_jira.project_issue_fields.assert_called_once_with("SWH", "10001")
        self.assertIn("Story", result)

    def test_issue_type_not_found(self):
        """Test handling when issue type doesn't exist."""
        self.mock_jira.project_issue_types.return_value = self.mock_issue_types

        with self.assertRaises(ValueError) as context:
            get_jira_fields(jira_instance=self.mock_jira, project_key="SWH", issue_type="NonExistent")

        self.assertIn("Issue type 'NonExistent' not found", str(context.exception))

    def test_no_issue_types_found(self):
        """Test handling when project has no issue types."""
        self.mock_jira.project_issue_types.return_value = []

        with self.assertRaises(ValueError) as context:
            get_jira_fields(jira_instance=self.mock_jira, project_key="SWH")

        self.assertIn("No issue types found for project SWH", str(context.exception))

    def test_no_fields_available(self):
        """Test handling empty fields list."""
        self.mock_jira.project_issue_types.return_value = self.mock_issue_types
        self.mock_jira.project_issue_fields.return_value = []

        result = get_jira_fields(jira_instance=self.mock_jira, project_key="SWH")

        # Verify appropriate message
        self.assertIn("No custom fields available", result)


class TestBuildFieldMap(unittest.TestCase):
    """Test cases for the build_field_map function.

    Tests field name to ID mapping functionality.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.mock_jira = Mock()
        self.mock_fields = [
            {"id": "summary", "name": "Summary"},
            {"id": "priority", "name": "Priority"},
            {"id": "customfield_10400", "name": "Definition of Done"},
        ]

    def test_build_field_map(self):
        """Test building field name to ID map."""
        self.mock_jira.fields.return_value = self.mock_fields

        field_map = build_field_map(self.mock_jira)

        # Verify lowercase name mapping
        self.assertEqual(field_map["summary"], "summary")
        self.assertEqual(field_map["priority"], "priority")
        self.assertEqual(field_map["definition of done"], "customfield_10400")

        # Verify ID to ID mapping
        self.assertEqual(field_map["summary"], "summary")
        self.assertEqual(field_map["customfield_10400"], "customfield_10400")

    def test_empty_fields(self):
        """Test building map with empty fields."""
        self.mock_jira.fields.return_value = []

        field_map = build_field_map(self.mock_jira)

        # Even with empty fields, fallback mappings should be present
        self.assertEqual(
            field_map,
            {
                "definition of done": "customfield_10400",
                "acceptance criteria": "customfield_10200",
            },
        )


class TestFormatFieldValue(unittest.TestCase):
    """Test cases for the format_field_value function.

    Tests value formatting for different field types.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.mock_jira = Mock()

    def test_format_priority_string(self):
        """Test formatting priority field with string value."""
        self.mock_jira.fields.return_value = [{"id": "priority", "name": "Priority", "schema": {"type": "priority"}}]

        result = format_field_value("priority", "High", self.mock_jira)

        self.assertEqual(result, {"name": "High"})

    def test_format_priority_dict(self):
        """Test formatting priority field with dict value."""
        self.mock_jira.fields.return_value = [{"id": "priority", "name": "Priority", "schema": {"type": "priority"}}]

        result = format_field_value("priority", {"name": "High"}, self.mock_jira)

        self.assertEqual(result, {"name": "High"})

    def test_format_assignee_string(self):
        """Test formatting assignee field with string value."""
        self.mock_jira.fields.return_value = [{"id": "assignee", "name": "Assignee", "schema": {"type": "user"}}]

        result = format_field_value("assignee", "john.doe", self.mock_jira)

        self.assertEqual(result, {"name": "john.doe"})

    def test_format_assignee_none(self):
        """Test formatting assignee field with None (unassign)."""
        self.mock_jira.fields.return_value = [{"id": "assignee", "name": "Assignee", "schema": {"type": "user"}}]

        result = format_field_value("assignee", None, self.mock_jira)

        self.assertIsNone(result)

    def test_format_labels_list(self):
        """Test formatting labels field with list value."""
        self.mock_jira.fields.return_value = [{"id": "labels", "name": "Labels", "schema": {"type": "array"}}]

        result = format_field_value("labels", ["bug", "urgent"], self.mock_jira)

        self.assertEqual(result, ["bug", "urgent"])

    def test_format_labels_string(self):
        """Test formatting labels field with comma-separated string."""
        self.mock_jira.fields.return_value = [{"id": "labels", "name": "Labels", "schema": {"type": "array"}}]

        result = format_field_value("labels", "bug, urgent", self.mock_jira)

        self.assertEqual(result, ["bug", "urgent"])

    def test_format_components_list(self):
        """Test formatting components field with list of strings."""
        self.mock_jira.fields.return_value = [{"id": "components", "name": "Components", "schema": {"type": "array"}}]

        result = format_field_value("components", ["Frontend", "Backend"], self.mock_jira)

        self.assertEqual(result, [{"name": "Frontend"}, {"name": "Backend"}])

    def test_format_unknown_field(self):
        """Test formatting unknown field returns value as-is."""
        self.mock_jira.fields.return_value = []

        result = format_field_value("unknown_field", "some_value", self.mock_jira)

        self.assertEqual(result, "some_value")

    def test_format_definition_of_done_strings(self):
        """Test formatting Definition of Done field with list of strings."""
        self.mock_jira.fields.return_value = [
            {
                "id": "customfield_10400",
                "name": "Definition of Done",
                "schema": {"type": "array", "items": "json"},
            }
        ]

        result = format_field_value("customfield_10400", ["Task 1", "Task 2"], self.mock_jira)

        expected = [
            {"name": "Task 1", "checked": False, "mandatory": True},
            {"name": "Task 2", "checked": False, "mandatory": True},
        ]
        self.assertEqual(result, expected)

    def test_format_definition_of_done_by_name(self):
        """Test formatting Definition of Done field using field name."""
        self.mock_jira.fields.return_value = [
            {
                "id": "customfield_10400",
                "name": "Definition of Done",
                "schema": {"type": "array", "items": "json"},
            }
        ]

        result = format_field_value("Definition of Done", ["Task 1"], self.mock_jira)

        expected = [{"name": "Task 1", "checked": False, "mandatory": True}]
        self.assertEqual(result, expected)

    def test_format_acceptance_criteria_strings(self):
        """Test formatting Acceptance Criteria field with list of strings."""
        self.mock_jira.fields.return_value = [
            {
                "id": "customfield_10200",
                "name": "Acceptance Criteria",
                "schema": {"type": "array", "items": "json"},
            }
        ]

        result = format_field_value("customfield_10200", ["Criteria 1", "Criteria 2"], self.mock_jira)

        expected = [
            {"name": "Criteria 1", "checked": False, "mandatory": True},
            {"name": "Criteria 2", "checked": False, "mandatory": True},
        ]
        self.assertEqual(result, expected)

    def test_format_checklist_with_dicts(self):
        """Test formatting checklist field with pre-formatted dicts."""
        self.mock_jira.fields.return_value = [
            {
                "id": "customfield_10400",
                "name": "Definition of Done",
                "schema": {"type": "array", "items": "json"},
            }
        ]

        pre_formatted = [{"name": "Task 1", "checked": True, "mandatory": False}]
        result = format_field_value("customfield_10400", pre_formatted, self.mock_jira)

        # Should preserve pre-formatted items
        self.assertEqual(result, pre_formatted)

    def test_format_checklist_invalid_type(self):
        """Test formatting checklist field with invalid type."""
        self.mock_jira.fields.return_value = [
            {
                "id": "customfield_10400",
                "name": "Definition of Done",
                "schema": {"type": "array", "items": "json"},
            }
        ]

        result = format_field_value("customfield_10400", "not a list", self.mock_jira)

        self.assertIsNone(result)


class TestResolveFieldUpdates(unittest.TestCase):
    """Test cases for the resolve_field_updates function.

    Tests end-to-end field resolution and formatting.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.mock_jira = Mock()
        self.mock_jira.fields.return_value = [
            {"id": "summary", "name": "Summary", "schema": {"type": "string"}},
            {"id": "priority", "name": "Priority", "schema": {"type": "priority"}},
            {"id": "assignee", "name": "Assignee", "schema": {"type": "user"}},
            {"id": "labels", "name": "Labels", "schema": {"type": "array"}},
        ]

    def test_resolve_with_field_names(self):
        """Test resolving updates using field names."""
        updates = {"priority": "High", "assignee": "john.doe"}

        result = resolve_field_updates(updates, self.mock_jira)

        self.assertEqual(result["priority"], {"name": "High"})
        self.assertEqual(result["assignee"], {"name": "john.doe"})

    def test_resolve_with_field_ids(self):
        """Test resolving updates using field IDs."""
        updates = {"priority": "High", "assignee": "john.doe"}

        result = resolve_field_updates(updates, self.mock_jira)

        self.assertIn("priority", result)
        self.assertIn("assignee", result)

    def test_resolve_skips_none_values(self):
        """Test that None values are skipped."""
        updates = {"summary": "New title", "priority": None}

        result = resolve_field_updates(updates, self.mock_jira)

        self.assertIn("summary", result)
        self.assertNotIn("priority", result)

    def test_resolve_multiple_fields(self):
        """Test resolving multiple fields at once."""
        updates = {
            "summary": "New title",
            "priority": "High",
            "labels": ["bug", "urgent"],
        }

        result = resolve_field_updates(updates, self.mock_jira)

        self.assertEqual(result["summary"], "New title")
        self.assertEqual(result["priority"], {"name": "High"})
        self.assertEqual(result["labels"], ["bug", "urgent"])


if __name__ == "__main__":
    unittest.main()
