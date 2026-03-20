"""Tests for JIRA markdown rendering functionality."""

from unittest.mock import Mock

from ai_tools_jira.markdown_renderer import (
    convert_checkbox_list_to_text,
    format_field_for_display,
    render_issue_to_markdown,
)


class TestConvertCheckboxListToText:
    """Test the convert_checkbox_list_to_text function."""

    def test_empty_list(self):
        """Test that empty list creates proper section."""
        result = convert_checkbox_list_to_text("Test Title", [])
        expected = "\n\n## Test Title\n"
        assert result == expected

    def test_mixed_items(self):
        """Test that mixed headers and checklist items are rendered correctly."""
        # Mock checkbox items
        header_item = Mock()
        header_item.isHeader = True
        header_item.name = "Main Section"

        checked_item = Mock()
        checked_item.isHeader = False
        checked_item.checked = True
        checked_item.mandatory = False
        checked_item.name = "Completed task"

        unchecked_required_item = Mock()
        unchecked_required_item.isHeader = False
        unchecked_required_item.checked = False
        unchecked_required_item.mandatory = True
        unchecked_required_item.name = "Required task"

        items = [header_item, checked_item, unchecked_required_item]
        result = convert_checkbox_list_to_text("Test Criteria", items)

        expected = "\n\n## Test Criteria\n\nMain Section\n- [x] Completed task\n- [ ] Required task (required)\n"
        assert result == expected


class TestRenderIssueToMarkdown:
    """Test the render_issue_to_markdown function."""

    def create_mock_issue(self, **field_overrides):
        """Create a mock JIRA issue for testing."""
        issue = Mock()
        issue.key = "TEST-123"

        # Default fields
        fields = Mock()
        fields.summary = "Test Issue Title"
        fields.description = "Test issue description"
        fields.status = Mock()
        fields.status.name = "In Progress"
        fields.assignee = Mock()
        fields.assignee.displayName = "John Doe"
        fields.reporter = Mock()
        fields.reporter.displayName = "Jane Doe"
        fields.priority = Mock()
        fields.priority.name = "High"
        fields.components = []  # Components list
        fields.created = "2023-01-01T10:00:00.000+0000"
        fields.updated = "2023-01-02T10:00:00.000+0000"

        # Empty lists by default
        fields.comment = Mock()
        fields.comment.comments = []
        fields.attachment = []

        # Override with any provided values
        for key, value in field_overrides.items():
            setattr(fields, key, value)

        issue.fields = fields
        return issue

    def test_basic_issue_rendering(self):
        """Test rendering of a basic issue with standard fields."""
        issue = self.create_mock_issue()

        result = render_issue_to_markdown(issue)

        # Check that all basic elements are present
        assert "# Test Issue Title" in result
        assert "**Key:** TEST-123" in result
        assert "**Status:** In Progress" in result
        assert "**Assignee:** John Doe" in result
        assert "**Reporter:** Jane Doe" in result
        assert "**Priority:** High" in result
        assert "## Description\nTest issue description" in result

    def test_issue_with_attachments(self):
        """Test rendering of issue with attachments."""
        attachment = Mock()
        attachment.id = "12345"
        attachment.filename = "test_file.pdf"

        issue = self.create_mock_issue(attachment=[attachment])

        result = render_issue_to_markdown(issue)

        assert "## Attachments" in result
        assert "- 12345: test_file.pdf" in result

    def test_issue_with_comments(self):
        """Test rendering of issue with comments."""
        comment = Mock()
        comment.author = Mock()
        comment.author.displayName = "Bob Smith"
        comment.created = "2023-01-03T14:30:00.000+0000"
        comment.body = "This is a test comment"

        comment_list = Mock()
        comment_list.comments = [comment]

        issue = self.create_mock_issue(comment=comment_list)

        result = render_issue_to_markdown(issue)

        assert "## Comments" in result
        assert "**Bob Smith** (2023-01-03T14:30:00.000+0000):" in result
        assert "This is a test comment" in result

    def test_issue_with_components(self):
        """Test rendering of issue with components."""
        component1 = Mock()
        component1.name = "Backend"

        component2 = Mock()
        component2.name = "API"

        issue = self.create_mock_issue(components=[component1, component2])

        result = render_issue_to_markdown(issue)

        assert "**Components:** Backend, API" in result

    def test_issue_with_no_description(self):
        """Test rendering of issue with no description."""
        issue = self.create_mock_issue(description=None)

        result = render_issue_to_markdown(issue)

        assert "## Description\nNo description provided" in result

    def test_issue_missing_optional_fields(self):
        """Test rendering when optional fields are missing."""
        issue = Mock()
        issue.key = "TEST-456"

        fields = Mock()
        fields.summary = "Minimal Issue"
        fields.description = "Basic description"

        # Mock empty collections for required fields
        fields.comment = Mock()
        fields.comment.comments = []
        fields.attachment = []

        # Remove optional fields entirely
        del fields.status
        del fields.assignee
        del fields.reporter
        del fields.priority
        del fields.components
        del fields.created
        del fields.updated

        issue.fields = fields

        result = render_issue_to_markdown(issue)

        # Should still render basic info
        assert "# Minimal Issue" in result
        assert "**Key:** TEST-456" in result
        assert "## Description\nBasic description" in result

        # Should not contain optional fields
        assert "**Status:**" not in result


class TestFormatFieldForDisplay:
    """Test the format_field_for_display function."""

    def test_format_string_value(self):
        """Test formatting of string values."""
        result = format_field_for_display("test_field", "test value")
        assert result == "test value"

    def test_format_integer_value(self):
        """Test formatting of integer values."""
        result = format_field_for_display("test_field", 42)
        assert result == "42"

    def test_format_float_value(self):
        """Test formatting of float values."""
        result = format_field_for_display("test_field", 3.14)
        assert result == "3.14"

    def test_format_boolean_value(self):
        """Test formatting of boolean values."""
        result = format_field_for_display("test_field", True)
        assert result == "True"

    def test_format_none_value(self):
        """Test formatting of None values."""
        result = format_field_for_display("test_field", None)
        assert result is None

    def test_format_list_of_strings(self):
        """Test formatting of list of strings (e.g., labels)."""
        result = format_field_for_display("labels", ["bug", "urgent", "high-priority"])
        assert result == "bug, urgent, high-priority"

    def test_format_empty_list(self):
        """Test formatting of empty list."""
        result = format_field_for_display("labels", [])
        assert result is None

    def test_format_list_of_objects_with_name(self):
        """Test formatting of list of objects with name attribute (e.g., components)."""
        mock_obj1 = Mock()
        mock_obj1.name = "Backend"
        mock_obj2 = Mock()
        mock_obj2.name = "API"

        result = format_field_for_display("components", [mock_obj1, mock_obj2])
        assert result == "Backend, API"

    def test_format_object_with_name(self):
        """Test formatting of object with name attribute (e.g., status)."""
        mock_obj = Mock()
        mock_obj.name = "In Progress"

        result = format_field_for_display("status", mock_obj)
        assert result == "In Progress"

    def test_format_object_with_displayname(self):
        """Test formatting of object with displayName attribute (e.g., user)."""
        mock_user = Mock()
        mock_user.displayName = "John Doe"
        delattr(mock_user, "name")  # Ensure it doesn't have name attribute

        result = format_field_for_display("assignee", mock_user)
        assert result == "John Doe"
