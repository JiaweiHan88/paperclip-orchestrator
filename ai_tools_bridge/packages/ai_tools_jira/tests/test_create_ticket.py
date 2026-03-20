"""Tests for JIRA ticket creation functionality."""

import unittest
from unittest.mock import Mock

from ai_tools_jira.create_ticket import CreateJiraTicketInput, create_jira_ticket


class TestCreateJiraTicket(unittest.TestCase):
    """Test cases for JIRA ticket creation."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_input = CreateJiraTicketInput(
            project_key="TEST",
            issue_type="Story",
            summary="Test ticket",
            description="This is a test ticket",
            assignee="john.doe",
            priority="High",
        )

    def test_create_jira_ticket_success(self):
        """Test successful JIRA ticket creation."""
        # Setup mock JIRA instance
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.key = "TEST-123"
        mock_jira.create_issue.return_value = mock_issue
        mock_jira.server_url = "https://jira.example.com"

        # Call function
        result = create_jira_ticket(
            project_key=self.sample_input.project_key,
            issue_type=self.sample_input.issue_type,
            summary=self.sample_input.summary,
            description=self.sample_input.description,
            jira_instance=mock_jira,
            assignee=self.sample_input.assignee,
            priority=self.sample_input.priority,
        )

        # Verify JIRA instance was created with token

        # Verify create_issue was called with correct fields
        mock_jira.create_issue.assert_called_once()
        call_args = mock_jira.create_issue.call_args[1]["fields"]

        self.assertEqual(call_args["project"]["key"], "TEST")
        self.assertEqual(call_args["summary"], "Test ticket")
        self.assertEqual(call_args["description"], "This is a test ticket")
        self.assertEqual(call_args["issuetype"]["name"], "Story")
        self.assertEqual(call_args["assignee"]["name"], "john.doe")
        self.assertEqual(call_args["priority"]["name"], "High")

        # Verify result contains expected information
        self.assertIn("TEST-123", result)
        self.assertIn("JIRA Ticket Created Successfully", result)
        # The actual implementation only returns a simple success message
        self.assertEqual(result, "JIRA Ticket Created Successfully TEST-123")

    def test_create_jira_ticket_minimal(self):
        """Test JIRA ticket creation with minimal required fields."""
        # Setup mock JIRA instance
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.key = "TEST-456"
        mock_jira.create_issue.return_value = mock_issue
        mock_jira.server_url = "https://jira.example.com"

        # Call function with minimal parameters
        result = create_jira_ticket(
            project_key="TEST",
            issue_type="Bug",
            summary="Bug fix",
            description="Fix the bug",
            jira_instance=mock_jira,
        )

        # Verify create_issue was called
        mock_jira.create_issue.assert_called_once()
        call_args = mock_jira.create_issue.call_args[1]["fields"]

        # Verify optional fields are not included
        self.assertNotIn("assignee", call_args)
        self.assertNotIn("priority", call_args)

        # Verify result
        self.assertIn("TEST-456", result)
        self.assertIn("JIRA Ticket Created Successfully", result)
        # The actual implementation only returns a simple success message
        self.assertEqual(result, "JIRA Ticket Created Successfully TEST-456")

    def test_create_jira_ticket_empty_optionals(self):
        """Test JIRA ticket creation with empty optional fields."""
        # Setup mock JIRA instance
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.key = "TEST-789"
        mock_jira.create_issue.return_value = mock_issue
        mock_jira.server_url = "https://jira.example.com"

        # Call function with empty optional lists
        result = create_jira_ticket(
            project_key="TEST",
            issue_type="Task",
            summary="Simple task",
            description="Task with no DoD or AC",
            jira_instance=mock_jira,
        )

        # Verify create_issue was called
        mock_jira.create_issue.assert_called_once()

        # Verify result contains the expected simple success message
        self.assertIn("TEST-789", result)
        self.assertIn("JIRA Ticket Created Successfully", result)
        # The actual implementation only returns a simple success message
        self.assertEqual(result, "JIRA Ticket Created Successfully TEST-789")

    def test_create_jira_ticket_input_validation(self):
        """Test that the input model validates correctly."""
        # Valid input should work
        valid_input = CreateJiraTicketInput(
            project_key="PROJ",
            issue_type="Task",
            summary="Test",
            description="Test description",
        )
        self.assertEqual(valid_input.project_key, "PROJ")

        # Test field examples are properly set
        self.assertIn("SWH", CreateJiraTicketInput.model_fields["project_key"].examples)
        self.assertIn("Story", CreateJiraTicketInput.model_fields["issue_type"].examples)

    def test_create_jira_ticket_with_components(self):
        """Test JIRA ticket creation with components."""
        # Setup mock JIRA instance
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.key = "TEST-999"
        mock_jira.create_issue.return_value = mock_issue
        mock_jira.server_url = "https://jira.example.com"

        # Call function with components
        result = create_jira_ticket(
            project_key="TEST",
            issue_type="Story",
            summary="Feature with components",
            description="Feature description",
            jira_instance=mock_jira,
            components=["Backend", "API"],
        )

        # Verify create_issue was called
        mock_jira.create_issue.assert_called_once()
        call_args = mock_jira.create_issue.call_args[1]["fields"]

        # Verify components are formatted correctly
        expected_components = [{"name": "Backend"}, {"name": "API"}]
        self.assertEqual(call_args["components"], expected_components)

        # Verify result
        self.assertIn("TEST-999", result)
        self.assertIn("JIRA Ticket Created Successfully", result)

    def test_create_jira_ticket_epic_with_epic_name(self):
        """Test JIRA Epic creation with Epic Name via custom_fields."""
        # Setup mock JIRA instance
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.key = "TEST-100"
        mock_jira.create_issue.return_value = mock_issue
        mock_jira.server_url = "https://jira.example.com"

        # Mock fields() to return field definitions for resolve_field_updates
        mock_jira.fields.return_value = [
            {
                "id": "customfield_10105",
                "name": "Epic Name",
                "custom": True,
                "schema": {"type": "string"},
            },
        ]

        # Call function with Epic type and Epic Name via custom_fields
        result = create_jira_ticket(
            project_key="TEST",
            issue_type="Epic",
            summary="New Epic for User Authentication",
            description="This epic covers all user authentication features",
            jira_instance=mock_jira,
            custom_fields={"Epic Name": "User Authentication"},
        )

        # Verify create_issue was called
        mock_jira.create_issue.assert_called_once()
        call_args = mock_jira.create_issue.call_args[1]["fields"]

        # Verify Epic Name (customfield_10105) is set
        self.assertEqual(call_args["customfield_10105"], "User Authentication")
        self.assertEqual(call_args["issuetype"]["name"], "Epic")

        # Verify result
        self.assertIn("TEST-100", result)
        self.assertIn("JIRA Ticket Created Successfully", result)

    def test_create_jira_ticket_epic_without_epic_name(self):
        """Test JIRA Epic creation without Epic Name field (should not set customfield_10105)."""
        # Setup mock JIRA instance
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.key = "TEST-101"
        mock_jira.create_issue.return_value = mock_issue
        mock_jira.server_url = "https://jira.example.com"

        # Call function with Epic type but no epic_name
        result = create_jira_ticket(
            project_key="TEST",
            issue_type="Epic",
            summary="Epic without explicit name",
            description="This epic does not have an explicit epic name",
            jira_instance=mock_jira,
        )

        # Verify create_issue was called
        mock_jira.create_issue.assert_called_once()
        call_args = mock_jira.create_issue.call_args[1]["fields"]

        # Verify Epic Name (customfield_10105) is NOT set
        self.assertNotIn("customfield_10105", call_args)

        # Verify result
        self.assertIn("TEST-101", result)
        self.assertIn("JIRA Ticket Created Successfully", result)

    def test_create_jira_ticket_with_custom_fields(self):
        """Test JIRA ticket creation with custom fields."""
        # Setup mock JIRA instance
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.key = "TEST-103"
        mock_jira.create_issue.return_value = mock_issue
        mock_jira.server_url = "https://jira.example.com"

        # Mock fields() to return field definitions for resolve_field_updates
        mock_jira.fields.return_value = [
            {"id": "customfield_10600", "name": "Parent Link", "custom": True, "schema": {"type": "string"}},
            {"id": "customfield_10700", "name": "Epic Link", "custom": True, "schema": {"type": "string"}},
        ]

        # Call function with custom_fields
        result = create_jira_ticket(
            project_key="TEST",
            issue_type="Story",
            summary="Story with custom fields",
            description="Story with Parent Link",
            jira_instance=mock_jira,
            custom_fields={"Parent Link": "TEST-200"},
        )

        # Verify create_issue was called
        mock_jira.create_issue.assert_called_once()
        call_args = mock_jira.create_issue.call_args[1]["fields"]

        # Verify custom field is set (resolved to field ID)
        self.assertEqual(call_args["customfield_10600"], "TEST-200")

        # Verify result
        self.assertIn("TEST-103", result)
        self.assertIn("JIRA Ticket Created Successfully", result)

    def test_create_jira_ticket_epic_with_custom_fields(self):
        """Test JIRA Epic creation with Epic Name and other custom fields."""
        # Setup mock JIRA instance
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.key = "TEST-104"
        mock_jira.create_issue.return_value = mock_issue
        mock_jira.server_url = "https://jira.example.com"

        # Mock fields() to return field definitions for resolve_field_updates
        mock_jira.fields.return_value = [
            {"id": "customfield_10105", "name": "Epic Name", "custom": True, "schema": {"type": "string"}},
            {"id": "customfield_10600", "name": "Parent Link", "custom": True, "schema": {"type": "string"}},
        ]

        # Call function with Epic type and multiple custom fields
        result = create_jira_ticket(
            project_key="TEST",
            issue_type="Epic",
            summary="Epic with custom fields",
            description="Epic with Parent Link",
            jira_instance=mock_jira,
            custom_fields={"Epic Name": "My Epic Name", "Parent Link": "TEST-300"},
        )

        # Verify create_issue was called
        mock_jira.create_issue.assert_called_once()
        call_args = mock_jira.create_issue.call_args[1]["fields"]

        # Verify Epic Name (customfield_10105) is set
        self.assertEqual(call_args["customfield_10105"], "My Epic Name")
        # Verify custom field is also set
        self.assertEqual(call_args["customfield_10600"], "TEST-300")
        self.assertEqual(call_args["issuetype"]["name"], "Epic")

        # Verify result
        self.assertIn("TEST-104", result)
        self.assertIn("JIRA Ticket Created Successfully", result)


if __name__ == "__main__":
    unittest.main()
