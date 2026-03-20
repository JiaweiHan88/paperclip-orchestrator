"""Tests for Jira issue functionality.

This module contains comprehensive tests for fetching and formatting Jira issues,
including success cases, error handling, and edge cases.
"""

import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from ai_tools_jira.issue import JiraIssueInput, get_jira_issue


class TestJiraIssueInput(unittest.TestCase):
    """Test cases for the JiraIssueInput Pydantic model.

    Tests validation of input parameters and model behavior.
    """

    def test_valid_input_with_project_key(self):
        """Test that model accepts valid input with project-style key."""
        input_data = JiraIssueInput(key="SWH-456")
        self.assertEqual(input_data.key, "SWH-456")

    def test_valid_input_with_mcp_key(self):
        """Test that model accepts valid input with MCP-style key."""
        input_data = JiraIssueInput(key="MCP-789")
        self.assertEqual(input_data.key, "MCP-789")

    def test_valid_input_with_numeric_key(self):
        """Test that model accepts valid input with numeric key."""
        input_data = JiraIssueInput(key="PROJECT-123")
        self.assertEqual(input_data.key, "PROJECT-123")

    def test_empty_key_accepted(self):
        """Test that empty key is accepted (no explicit validation)."""
        input_data = JiraIssueInput(key="")
        self.assertEqual(input_data.key, "")

    def test_missing_key_raises_validation_error(self):
        """Test that missing key raises ValidationError."""
        with self.assertRaises(ValidationError):
            JiraIssueInput()

    def test_whitespace_key_accepted(self):
        """Test that whitespace-only key is accepted (no explicit validation)."""
        input_data = JiraIssueInput(key="   ")
        self.assertEqual(input_data.key, "   ")

    def test_valid_input_with_fields(self):
        """Test that model accepts fields parameter."""
        input_data = JiraIssueInput(key="SWH-456", fields=["labels", "components"])
        self.assertEqual(input_data.key, "SWH-456")
        self.assertEqual(input_data.fields, ["labels", "components"])

    def test_valid_input_with_fields_empty_list(self):
        """Test that model accepts fields parameter with empty list (all fields)."""
        input_data = JiraIssueInput(key="SWH-456", fields=[])
        self.assertEqual(input_data.key, "SWH-456")
        self.assertEqual(input_data.fields, [])


class TestGetJiraIssue(unittest.TestCase):
    """Test cases for the get_jira_issue function.

    Tests successful issue retrieval, error conditions, and markdown formatting
    using mocks to avoid actual API calls.
    """

    def setUp(self):
        """Set up test fixtures and common test data."""
        self.key = "SWH-456"

        # Mock issue with all fields
        self.mock_issue = Mock()
        self.mock_issue.fields.summary = "Test Issue Title"
        self.mock_issue.fields.description = "This is a test issue description"
        self.mock_issue.fields.components = []

        # Mock comments
        self.mock_comment1 = Mock()
        self.mock_comment1.author.displayName = "John Doe"
        self.mock_comment1.created = "2023-01-15T10:30:00.000+0000"
        self.mock_comment1.body = "This is the first comment"

        self.mock_comment2 = Mock()
        self.mock_comment2.author.displayName = "Jane Smith"
        self.mock_comment2.created = "2023-01-16T14:45:00.000+0000"
        self.mock_comment2.body = "This is the second comment"

        self.mock_issue.fields.comment.comments = [self.mock_comment1, self.mock_comment2]

        # Mock attachments
        self.mock_attachment1 = Mock()
        self.mock_attachment1.id = "att-001"
        self.mock_attachment1.filename = "document.pdf"

        self.mock_attachment2 = Mock()
        self.mock_attachment2.id = "att-002"
        self.mock_attachment2.filename = "screenshot.png"

        self.mock_issue.fields.attachment = [self.mock_attachment1, self.mock_attachment2]

        # Create mock JIRA instance
        self.mock_jira = Mock()
        self.mock_jira.issue.return_value = self.mock_issue

    def test_successful_issue_retrieval_with_all_fields(self):
        """Test successful issue retrieval with all fields present."""
        # Call function with mock jira instance
        result = get_jira_issue(key=self.key, jira_instance=self.mock_jira)

        # Verify API calls
        self.mock_jira.issue.assert_called_once_with(self.key)

        # Verify output format
        self.assertIn("# Test Issue Title", result)
        self.assertIn("## Description", result)
        self.assertIn("This is a test issue description", result)
        self.assertIn("## Attachments", result)
        self.assertIn("- att-001: document.pdf", result)
        self.assertIn("- att-002: screenshot.png", result)
        self.assertIn("## Comments", result)
        self.assertIn("**John Doe** (2023-01-15T10:30:00.000+0000):", result)
        self.assertIn("This is the first comment", result)
        self.assertIn("**Jane Smith** (2023-01-16T14:45:00.000+0000):", result)
        self.assertIn("This is the second comment", result)

    def test_issue_with_no_description(self):
        """Test issue retrieval when description is None."""
        # Setup mock with no description
        mock_issue = Mock()
        mock_issue.fields.summary = "Issue Without Description"
        mock_issue.fields.description = None
        mock_issue.fields.components = []
        mock_issue.fields.comment.comments = []
        mock_issue.fields.attachment = []

        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue

        # Call function
        result = get_jira_issue(key=self.key, jira_instance=mock_jira)

        # Verify output
        self.assertIn("# Issue Without Description", result)
        self.assertIn("## Description", result)
        self.assertIn("No description provided", result)
        self.assertNotIn("## Attachments", result)
        self.assertNotIn("## Comments", result)

    def test_issue_with_empty_comments_and_attachments(self):
        """Test issue retrieval with empty comments and attachments lists."""
        # Setup mock with empty lists
        mock_issue = Mock()
        mock_issue.fields.summary = "Minimal Issue"
        mock_issue.fields.description = "Simple description"
        mock_issue.fields.components = []
        mock_issue.fields.comment.comments = []
        mock_issue.fields.attachment = []

        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue

        # Call function
        result = get_jira_issue(key=self.key, jira_instance=mock_jira)

        # Verify output
        self.assertIn("# Minimal Issue", result)
        self.assertIn("## Description", result)
        self.assertIn("Simple description", result)
        self.assertNotIn("## Attachments", result)
        self.assertNotIn("## Comments", result)

    def test_issue_with_only_comments(self):
        """Test issue retrieval with comments but no attachments."""
        # Setup mock with only comments
        mock_issue = Mock()
        mock_issue.fields.summary = "Issue With Comments Only"
        mock_issue.fields.description = "Issue description"
        mock_issue.fields.components = []
        mock_issue.fields.comment.comments = [self.mock_comment1]
        mock_issue.fields.attachment = []

        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue

        # Call function
        result = get_jira_issue(key=self.key, jira_instance=mock_jira)

        # Verify output
        self.assertIn("# Issue With Comments Only", result)
        self.assertIn("## Comments", result)
        self.assertIn("**John Doe**", result)
        self.assertNotIn("## Attachments", result)

    def test_issue_with_only_attachments(self):
        """Test issue retrieval with attachments but no comments."""
        # Setup mock with only attachments
        mock_issue = Mock()
        mock_issue.fields.summary = "Issue With Attachments Only"
        mock_issue.fields.description = "Issue description"
        mock_issue.fields.components = []
        mock_issue.fields.comment.comments = []
        mock_issue.fields.attachment = [self.mock_attachment1]

        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue

        # Call function
        result = get_jira_issue(key=self.key, jira_instance=mock_jira)

        # Verify output
        self.assertIn("# Issue With Attachments Only", result)
        self.assertIn("## Attachments", result)
        self.assertIn("- att-001: document.pdf", result)
        self.assertNotIn("## Comments", result)

    def test_jira_api_exception_propagated(self):
        """Test that JIRA API exceptions are properly propagated."""
        # Setup mock to raise exception
        mock_jira = Mock()
        mock_jira.issue.side_effect = Exception("JIRA API Error")

        # Call function and expect exception
        with self.assertRaises(Exception) as context:
            get_jira_issue(key=self.key, jira_instance=mock_jira)

        self.assertEqual(str(context.exception), "JIRA API Error")

    def test_get_cc_jira_instance_called_with_correct_token(self):
        """Test that jira instance is used correctly."""
        # Setup mock
        mock_jira = Mock()
        mock_jira.issue.return_value = self.mock_issue

        # Call function
        get_jira_issue(key=self.key, jira_instance=mock_jira)

        # Verify jira.issue was called with the correct key
        mock_jira.issue.assert_called_once_with(self.key)

    def test_markdown_format_structure(self):
        """Test that the returned markdown follows expected structure."""
        # Setup minimal mock
        mock_issue = Mock()
        mock_issue.fields.summary = "Test Title"
        mock_issue.fields.description = "Test Description"
        mock_issue.fields.components = []
        mock_issue.fields.comment.comments = []
        mock_issue.fields.attachment = []

        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue

        # Call function
        result = get_jira_issue(key=self.key, jira_instance=mock_jira)

        # Verify markdown structure
        lines = result.split("\n")
        self.assertTrue(lines[0].startswith("# "))  # Title header
        self.assertIn("## Description", result)  # Description section
        self.assertTrue(result.endswith("\n"))  # Ends with newline

    def test_issue_with_fields_labels(self):
        """Test that fields parameter includes labels in the output."""
        # Setup mock with labels
        mock_issue = Mock()
        mock_issue.key = self.key
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = "Test Description"
        mock_issue.fields.comment.comments = []
        mock_issue.fields.attachment = []
        mock_issue.fields.labels = ["bug", "urgent"]

        # Mock for field discovery
        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue
        mock_jira.fields.return_value = [
            {"id": "labels", "name": "Labels"},
        ]

        # Call function with fields
        result = get_jira_issue(key=self.key, jira_instance=mock_jira, fields=["labels"])

        # Verify labels are in the output
        self.assertIn("## Additional Fields", result)
        self.assertIn("Labels", result)
        self.assertIn("bug, urgent", result)

    def test_issue_with_fields_components(self):
        """Test that components are displayed in default fields section."""
        # Setup mock with components
        mock_issue = Mock()
        mock_issue.key = self.key
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = "Test Description"
        mock_issue.fields.comment.comments = []
        mock_issue.fields.attachment = []

        mock_component1 = Mock()
        mock_component1.name = "Backend"
        mock_component2 = Mock()
        mock_component2.name = "API"
        mock_issue.fields.components = [mock_component1, mock_component2]

        # Mock for field discovery
        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue

        # Call function without fields parameter since components is a default field
        result = get_jira_issue(key=self.key, jira_instance=mock_jira)

        # Verify components are in the default output
        self.assertIn("**Components:** Backend, API", result)
        self.assertIn("Backend, API", result)

    def test_issue_with_fields_empty_list_includes_all(self):
        """Test that fields=[] includes all available fields."""
        # Setup mock with various fields including custom ones
        mock_issue = Mock()
        mock_issue.key = self.key
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = "Test Description"
        mock_issue.fields.comment.comments = []
        mock_issue.fields.attachment = []
        mock_issue.fields.labels = ["bug", "urgent"]
        mock_issue.fields.customfield_10100 = "Custom Value"
        mock_issue.fields.fixVersions = []  # Empty list should be excluded
        mock_issue.fields.duedate = "2023-12-31"

        # Mock for field discovery
        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue
        mock_jira.fields.return_value = [
            {"id": "labels", "name": "Labels"},
            {"id": "customfield_10100", "name": "Epic Link"},
            {"id": "duedate", "name": "Due Date"},
            {"id": "fixVersions", "name": "Fix Version/s"},
        ]

        # Call function with fields=[]
        result = get_jira_issue(key=self.key, jira_instance=mock_jira, fields=[])

        # Verify additional fields section exists
        self.assertIn("## Additional Fields", result)

        # Verify custom and non-default fields are included
        self.assertIn("Labels", result)
        self.assertIn("bug, urgent", result)
        self.assertIn("Epic Link", result)
        self.assertIn("Custom Value", result)
        self.assertIn("Due Date", result)
        self.assertIn("2023-12-31", result)

        # Verify empty fields are not included
        self.assertNotIn("Fix Version/s", result)

    def test_issue_with_fields_empty_list_excludes_default_fields(self):
        """Test that fields=[] doesn't duplicate default fields in Additional Fields section."""
        # Setup mock with default fields
        mock_issue = Mock()
        mock_issue.key = self.key
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = "Test Description"
        mock_issue.fields.status = Mock()
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.assignee = Mock()
        mock_issue.fields.assignee.displayName = "John Doe"
        mock_issue.fields.comment.comments = []
        mock_issue.fields.attachment = []
        mock_issue.fields.created = "2023-01-01T10:00:00.000+0000"
        mock_issue.fields.updated = "2023-01-02T10:00:00.000+0000"
        mock_issue.fields.labels = ["test"]

        # Mock for field discovery
        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue
        mock_jira.fields.return_value = [
            {"id": "summary", "name": "Summary"},
            {"id": "status", "name": "Status"},
            {"id": "assignee", "name": "Assignee"},
            {"id": "labels", "name": "Labels"},
        ]

        # Call function with fields=[]
        result = get_jira_issue(key=self.key, jira_instance=mock_jira, fields=[])

        # Verify default fields appear in their normal sections
        self.assertIn("**Status:** Open", result)
        self.assertIn("**Assignee:** John Doe", result)

        # Count occurrences of "Status" and "Assignee" - should only appear once each in default section
        # They should NOT appear in Additional Fields section
        lines = result.split("\n")
        additional_fields_section = False
        for line in lines:
            if "## Additional Fields" in line:
                additional_fields_section = True
            if additional_fields_section:
                # These default fields should not appear in Additional Fields section
                self.assertNotIn("**Status**:", line)
                self.assertNotIn("**Assignee**:", line)
                self.assertNotIn("**Summary**:", line)

    def test_issue_fields_empty_list_includes_all_not_just_requested(self):
        """Test that fields=[] includes all fields, not just a subset."""
        # Setup mock
        mock_issue = Mock()
        mock_issue.key = self.key
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = "Test Description"
        mock_issue.fields.comment.comments = []
        mock_issue.fields.attachment = []
        mock_issue.fields.labels = ["test"]
        mock_issue.fields.customfield_10200 = "Story Points: 5"
        mock_issue.fields.environment = "Production"

        # Mock for field discovery
        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue
        mock_jira.fields.return_value = [
            {"id": "labels", "name": "Labels"},
            {"id": "customfield_10200", "name": "Story Points"},
            {"id": "environment", "name": "Environment"},
        ]

        # Call function with fields=[] which should include all fields
        result = get_jira_issue(key=self.key, jira_instance=mock_jira, fields=[])

        # Verify all fields are included, not just labels
        self.assertIn("## Additional Fields", result)
        self.assertIn("Labels", result)
        self.assertIn("Story Points", result)
        self.assertIn("Environment", result)

    def test_issue_with_fields_empty_list_no_additional_fields(self):
        """Test that fields=[] correctly filters out methods and only default fields remain."""
        # Setup mock with only default fields - use spec to limit available attributes
        mock_issue = Mock()
        mock_issue.key = self.key

        # Create a simple object to avoid Mock methods appearing as fields
        class SimpleFields:
            summary = "Test Issue"
            description = "Test Description"
            status = None
            assignee = None
            reporter = None
            priority = None
            components = []
            created = None
            updated = None

            def __init__(self):
                self.comment = Mock()
                self.comment.comments = []
                self.attachment = []

        mock_issue.fields = SimpleFields()

        # Mock for field discovery
        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue
        mock_jira.fields.return_value = [
            {"id": "summary", "name": "Summary"},
            {"id": "description", "name": "Description"},
            {"id": "status", "name": "Status"},
            {"id": "assignee", "name": "Assignee"},
            {"id": "reporter", "name": "Reporter"},
            {"id": "priority", "name": "Priority"},
            {"id": "components", "name": "Components"},
            {"id": "created", "name": "Created"},
            {"id": "updated", "name": "Updated"},
            {"id": "comment", "name": "Comment"},
            {"id": "attachment", "name": "Attachment"},
        ]

        # Call function with fields=[]
        result = get_jira_issue(key=self.key, jira_instance=mock_jira, fields=[])

        # Verify no Additional Fields section when all fields are default fields
        # (all fields present are in the already_displayed set)
        self.assertNotIn("## Additional Fields", result)

        # Verify basic issue is still rendered
        self.assertIn("# Test Issue", result)
        self.assertIn("## Description", result)


if __name__ == "__main__":
    unittest.main()
