"""Tests for Jira transitions functionality.

This module contains comprehensive tests for getting available transitions and
transitioning issues between statuses, including success cases, error handling,
and edge cases.
"""

import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from ai_tools_jira.transitions import (
    GetJiraTransitionsInput,
    TransitionJiraIssueInput,
    get_jira_transitions,
    transition_jira_issue,
)


class TestGetJiraTransitionsInput(unittest.TestCase):
    """Test cases for the GetJiraTransitionsInput Pydantic model.

    Tests validation of input parameters and model behavior.
    """

    def test_valid_input_with_project_key(self):
        """Test that model accepts valid input with project-style key."""
        input_data = GetJiraTransitionsInput(issue_key="SWH-456")
        self.assertEqual(input_data.issue_key, "SWH-456")

    def test_valid_input_with_mcp_key(self):
        """Test that model accepts valid input with MCP-style key."""
        input_data = GetJiraTransitionsInput(issue_key="MCP-789")
        self.assertEqual(input_data.issue_key, "MCP-789")

    def test_missing_issue_key_raises_validation_error(self):
        """Test that missing issue_key raises ValidationError."""
        with self.assertRaises(ValidationError):
            GetJiraTransitionsInput()

    def test_empty_issue_key_accepted(self):
        """Test that empty issue_key is accepted (no explicit validation)."""
        input_data = GetJiraTransitionsInput(issue_key="")
        self.assertEqual(input_data.issue_key, "")


class TestTransitionJiraIssueInput(unittest.TestCase):
    """Test cases for the TransitionJiraIssueInput Pydantic model.

    Tests validation of input parameters and model behavior.
    """

    def test_valid_input_minimal(self):
        """Test that model accepts minimal valid input."""
        input_data = TransitionJiraIssueInput(issue_key="SWH-456", transition_id="11")
        self.assertEqual(input_data.issue_key, "SWH-456")
        self.assertEqual(input_data.transition_id, "11")
        self.assertIsNone(input_data.fields)

    def test_valid_input_with_all_fields(self):
        """Test that model accepts valid input with all fields."""
        input_data = TransitionJiraIssueInput(
            issue_key="MCP-789",
            transition_id="21",
            fields={"resolution": {"name": "Fixed"}},
        )
        self.assertEqual(input_data.issue_key, "MCP-789")
        self.assertEqual(input_data.transition_id, "21")
        self.assertEqual(input_data.fields, {"resolution": {"name": "Fixed"}})

    def test_missing_issue_key_raises_validation_error(self):
        """Test that missing issue_key raises ValidationError."""
        with self.assertRaises(ValidationError):
            TransitionJiraIssueInput(transition_id="11")

    def test_missing_transition_id_raises_validation_error(self):
        """Test that missing transition_id raises ValidationError."""
        with self.assertRaises(ValidationError):
            TransitionJiraIssueInput(issue_key="SWH-456")


class TestGetJiraTransitions(unittest.TestCase):
    """Test cases for the get_jira_transitions function.

    Tests successful retrieval of available transitions using mocks to avoid
    actual API calls.
    """

    def setUp(self):
        """Set up test fixtures and common test data."""
        self.issue_key = "SWH-456"

        # Create mock JIRA instance
        self.mock_jira = Mock()

    def test_successful_transitions_retrieval_with_status(self):
        """Test successful retrieval of transitions with target status."""
        # Mock transitions data
        mock_transitions = [
            {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
            {"id": "21", "name": "Done", "to": {"name": "Done"}},
            {"id": "31", "name": "Close Issue", "to": {"name": "Closed"}},
        ]
        self.mock_jira.transitions.return_value = mock_transitions

        # Call function
        result = get_jira_transitions(issue_key=self.issue_key, jira_instance=self.mock_jira)

        # Verify jira.transitions was called correctly
        self.mock_jira.transitions.assert_called_once_with(self.issue_key)

        # Verify result format
        self.assertIn(f"Available Transitions for {self.issue_key}", result)
        self.assertIn("Start Progress", result)
        self.assertIn("ID: `11`", result)
        self.assertIn("→ In Progress", result)
        self.assertIn("Done", result)
        self.assertIn("ID: `21`", result)
        self.assertIn("→ Done", result)

    def test_successful_transitions_retrieval_without_status(self):
        """Test successful retrieval of transitions without target status."""
        # Mock transitions data without 'to' field
        mock_transitions = [
            {"id": "11", "name": "Start Progress"},
            {"id": "21", "name": "Done"},
        ]
        self.mock_jira.transitions.return_value = mock_transitions

        # Call function
        result = get_jira_transitions(issue_key=self.issue_key, jira_instance=self.mock_jira)

        # Verify result format (no arrow since no target status)
        self.assertIn("Start Progress", result)
        self.assertIn("ID: `11`", result)
        self.assertNotIn("→", result)

    def test_empty_transitions_list(self):
        """Test handling of empty transitions list."""
        # Mock empty transitions
        self.mock_jira.transitions.return_value = []

        # Call function
        result = get_jira_transitions(issue_key=self.issue_key, jira_instance=self.mock_jira)

        # Verify result
        self.assertEqual(result, f"No transitions available for issue {self.issue_key}")

    def test_transitions_with_missing_fields(self):
        """Test handling of transitions with missing id or name fields."""
        # Mock transitions with missing fields
        mock_transitions = [
            {"name": "Start Progress"},  # Missing id
            {"id": "21"},  # Missing name
            {"id": "31", "name": "Close Issue", "to": {"name": "Closed"}},
        ]
        self.mock_jira.transitions.return_value = mock_transitions

        # Call function
        result = get_jira_transitions(issue_key=self.issue_key, jira_instance=self.mock_jira)

        # Verify that it handles missing fields gracefully
        self.assertIn("Available Transitions", result)


class TestTransitionJiraIssue(unittest.TestCase):
    """Test cases for the transition_jira_issue function.

    Tests successful issue transitions with various parameters using mocks
    to avoid actual API calls.
    """

    def setUp(self):
        """Set up test fixtures and common test data."""
        self.issue_key = "SWH-456"
        self.transition_id = "21"

        # Create mock JIRA instance
        self.mock_jira = Mock()

        # Mock the updated issue after transition
        self.mock_issue = Mock()
        self.mock_issue.fields.status.name = "In Progress"
        self.mock_jira.issue.return_value = self.mock_issue

    def test_successful_transition_minimal(self):
        """Test successful transition with minimal parameters."""
        # Call function
        result = transition_jira_issue(
            issue_key=self.issue_key,
            transition_id=self.transition_id,
            jira_instance=self.mock_jira,
        )

        # Verify transition_issue was called correctly
        self.mock_jira.transition_issue.assert_called_once_with(self.issue_key, self.transition_id)

        # Verify issue was fetched to get current status
        self.mock_jira.issue.assert_called_once_with(self.issue_key)

        # Verify result format
        self.assertIn("Transition Successful", result)
        self.assertIn(f"Issue **{self.issue_key}**", result)
        self.assertIn("**Current Status:** In Progress", result)

    def test_successful_transition_with_fields(self):
        """Test successful transition with additional fields."""
        fields = {"resolution": {"name": "Fixed"}}

        # Call function
        result = transition_jira_issue(
            issue_key=self.issue_key,
            transition_id=self.transition_id,
            jira_instance=self.mock_jira,
            fields=fields,
        )

        # Verify transition_issue was called with fields
        self.mock_jira.transition_issue.assert_called_once_with(self.issue_key, self.transition_id, fields=fields)

        # Verify result
        self.assertIn("Transition Successful", result)

    def test_transition_updates_status(self):
        """Test that transition correctly updates and displays new status."""
        # Mock issue with updated status
        self.mock_issue.fields.status.name = "Done"

        # Call function
        result = transition_jira_issue(
            issue_key=self.issue_key,
            transition_id=self.transition_id,
            jira_instance=self.mock_jira,
        )

        # Verify the new status is in the result
        self.assertIn("**Current Status:** Done", result)


if __name__ == "__main__":
    unittest.main()
