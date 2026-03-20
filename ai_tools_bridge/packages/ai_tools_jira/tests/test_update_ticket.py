"""Tests for JIRA ticket update functionality."""

import unittest
from unittest.mock import Mock

from ai_tools_jira.update_ticket import UpdateJiraTicketInput, update_jira_ticket


class TestUpdateJiraTicketInput(unittest.TestCase):
    """Test cases for UpdateJiraTicketInput Pydantic model.

    Requirements:
    - Test validation of input parameters
    - Test field examples
    """

    def test_valid_input(self):
        """Test that model accepts valid input."""
        input_data = UpdateJiraTicketInput(
            issue_key="TEST-123",
            summary="New title",
            priority="High",
        )
        self.assertEqual(input_data.issue_key, "TEST-123")
        self.assertEqual(input_data.summary, "New title")
        self.assertEqual(input_data.priority, "High")

    def test_valid_input_with_custom_fields(self):
        """Test that model accepts custom field IDs."""
        input_data = UpdateJiraTicketInput(
            issue_key="TEST-123",
            custom_fields={"customfield_10400": [{"name": "Item 1"}]},
        )
        self.assertEqual(input_data.issue_key, "TEST-123")
        self.assertIn("customfield_10400", input_data.custom_fields)


class TestUpdateJiraTicket(unittest.TestCase):
    """Test cases for JIRA ticket update with field discovery.

    Requirements:
    - Test successful update with field resolution
    - Test update with minimal fields
    - Test update with no fields
    - Test field name resolution
    - Test custom field IDs
    """

    def setUp(self):
        """Set up test fixtures."""
        self.mock_jira = Mock()
        self.mock_issue = Mock()
        self.mock_issue.key = "TEST-123"
        self.mock_jira.issue.return_value = self.mock_issue

        # Mock fields for field discovery
        self.mock_fields = [
            {"id": "summary", "name": "Summary", "schema": {"type": "string"}},
            {"id": "priority", "name": "Priority", "schema": {"type": "priority"}},
            {"id": "assignee", "name": "Assignee", "schema": {"type": "user"}},
            {"id": "labels", "name": "Labels", "schema": {"type": "array"}},
            {"id": "customfield_10400", "name": "Definition of Done", "schema": {"type": "array"}},
        ]
        self.mock_jira.fields.return_value = self.mock_fields

    def test_update_jira_ticket_with_field_names(self):
        """Test successful JIRA ticket update using field names."""
        result = update_jira_ticket(
            issue_key="TEST-123", summary="New title", priority="High", jira_instance=self.mock_jira
        )

        # Verify issue was fetched
        self.mock_jira.issue.assert_called_once_with("TEST-123")

        # Verify update was called
        self.mock_issue.update.assert_called_once()
        call_args = self.mock_issue.update.call_args[1]["fields"]

        # Verify fields were resolved and formatted
        self.assertEqual(call_args["summary"], "New title")
        self.assertEqual(call_args["priority"], {"name": "High"})

        # Verify result
        self.assertIn("TEST-123", result)
        self.assertIn("Updated Successfully", result)

    def test_update_jira_ticket_with_field_ids(self):
        """Test JIRA ticket update using field IDs directly."""
        result = update_jira_ticket(
            issue_key="TEST-123",
            custom_fields={"customfield_10400": [{"name": "Item 1"}]},
            jira_instance=self.mock_jira,
        )

        # Verify update was called
        self.mock_issue.update.assert_called_once()
        call_args = self.mock_issue.update.call_args[1]["fields"]

        # Verify custom field was passed through
        self.assertEqual(call_args["customfield_10400"], [{"name": "Item 1"}])

        # Verify result
        self.assertIn("TEST-123", result)

    def test_update_jira_ticket_with_assignee(self):
        """Test JIRA ticket update with assignee field."""
        result = update_jira_ticket(issue_key="TEST-123", assignee="john.doe", jira_instance=self.mock_jira)

        # Verify update was called with formatted assignee
        call_args = self.mock_issue.update.call_args[1]["fields"]
        self.assertEqual(call_args["assignee"], {"name": "john.doe"})

    def test_update_jira_ticket_with_labels(self):
        """Test JIRA ticket update with labels field."""
        result = update_jira_ticket(issue_key="TEST-123", labels=["bug", "urgent"], jira_instance=self.mock_jira)

        # Verify update was called with labels
        call_args = self.mock_issue.update.call_args[1]["fields"]
        self.assertEqual(call_args["labels"], ["bug", "urgent"])

    def test_update_jira_ticket_mixed_fields(self):
        """Test JIRA ticket update with mixed field names and IDs."""
        result = update_jira_ticket(
            issue_key="TEST-123",
            summary="New title",
            custom_fields={"customfield_10400": [{"name": "Item 1"}]},
            jira_instance=self.mock_jira,
        )

        # Verify both field types were updated
        call_args = self.mock_issue.update.call_args[1]["fields"]
        self.assertEqual(call_args["summary"], "New title")
        self.assertEqual(call_args["customfield_10400"], [{"name": "Item 1"}])

    def test_update_jira_ticket_no_fields(self):
        """Test JIRA ticket update with empty fields dictionary."""
        result = update_jira_ticket(issue_key="TEST-123", jira_instance=self.mock_jira)

        # Verify update was NOT called
        self.mock_issue.update.assert_not_called()

        # Verify appropriate result message
        self.assertIn("No fields to update", result)

    def test_update_jira_ticket_with_none_values(self):
        """Test JIRA ticket update filters out None values."""
        result = update_jira_ticket(
            issue_key="TEST-123", summary="New title", priority=None, jira_instance=self.mock_jira
        )

        # Verify only non-None fields were updated
        call_args = self.mock_issue.update.call_args[1]["fields"]
        self.assertEqual(call_args["summary"], "New title")
        self.assertNotIn("priority", call_args)

    def test_update_jira_ticket_with_definition_of_done(self):
        """Test JIRA ticket update with Definition of Done checklist field."""
        result = update_jira_ticket(
            issue_key="TEST-123", definition_of_done=["Task 1", "Task 2", "Task 3"], jira_instance=self.mock_jira
        )

        # Verify update was called with properly formatted checklist
        call_args = self.mock_issue.update.call_args[1]["fields"]
        expected = [
            {"name": "Task 1", "checked": False, "mandatory": True},
            {"name": "Task 2", "checked": False, "mandatory": True},
            {"name": "Task 3", "checked": False, "mandatory": True},
        ]
        self.assertEqual(call_args["customfield_10400"], expected)

    def test_update_jira_ticket_with_acceptance_criteria(self):
        """Test JIRA ticket update with Acceptance Criteria checklist field."""
        # Add acceptance criteria to mock fields
        self.mock_jira.fields.return_value.append(
            {"id": "customfield_10200", "name": "Acceptance Criteria", "schema": {"type": "array"}}
        )

        result = update_jira_ticket(
            issue_key="TEST-123", acceptance_criteria=["Criteria 1", "Criteria 2"], jira_instance=self.mock_jira
        )

        # Verify update was called with properly formatted checklist
        call_args = self.mock_issue.update.call_args[1]["fields"]
        expected = [
            {"name": "Criteria 1", "checked": False, "mandatory": True},
            {"name": "Criteria 2", "checked": False, "mandatory": True},
        ]
        self.assertEqual(call_args["customfield_10200"], expected)


if __name__ == "__main__":
    unittest.main()
