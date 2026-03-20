"""Tests for JIRA link issues functionality."""

import unittest
from unittest.mock import Mock

from jira import JIRA

from ai_tools_jira.link_issues import LinkJiraIssuesInput, link_jira_issues


class TestLinkJiraIssues(unittest.TestCase):
    """Test cases for linking JIRA issues."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_input = LinkJiraIssuesInput(
            inward_issue="TEST-123",
            outward_issue="TEST-456",
            link_type="causes",
        )

    def test_link_jira_issues_success(self):
        """Test successful JIRA issue linking."""
        # Setup mock JIRA instance
        mock_jira = Mock(spec=JIRA)
        mock_jira.create_issue_link.return_value = Mock()

        # Call function
        result = link_jira_issues(
            inward_issue=self.sample_input.inward_issue,
            outward_issue=self.sample_input.outward_issue,
            link_type=self.sample_input.link_type,
            jira_instance=mock_jira,
        )

        # Verify link was created
        mock_jira.create_issue_link.assert_called_once_with(
            type="causes", inwardIssue="TEST-123", outwardIssue="TEST-456"
        )

        # Verify result
        expected_result = "✅ Successfully linked TEST-123 causes TEST-456"
        self.assertEqual(result, expected_result)

    def test_link_jira_issues_with_blocks_type(self):
        """Test linking JIRA issues with 'blocks' relationship."""
        # Setup mock JIRA instance
        mock_jira = Mock(spec=JIRA)
        mock_jira.create_issue_link.return_value = Mock()

        # Call function
        result = link_jira_issues(
            inward_issue="PROJ-100",
            outward_issue="PROJ-200",
            link_type="blocks",
            jira_instance=mock_jira,
        )

        # Verify link was created with correct type
        mock_jira.create_issue_link.assert_called_once_with(
            type="blocks", inwardIssue="PROJ-100", outwardIssue="PROJ-200"
        )

        # Verify result
        expected_result = "✅ Successfully linked PROJ-100 blocks PROJ-200"
        self.assertEqual(result, expected_result)

    def test_link_jira_issues_with_relates_type(self):
        """Test linking JIRA issues with 'relates' relationship."""
        # Setup mock JIRA instance
        mock_jira = Mock(spec=JIRA)
        mock_jira.create_issue_link.return_value = Mock()

        # Call function
        result = link_jira_issues(
            inward_issue="BUG-111",
            outward_issue="BUG-222",
            link_type="relates",
            jira_instance=mock_jira,
        )

        # Verify link was created with correct type
        mock_jira.create_issue_link.assert_called_once_with(
            type="relates", inwardIssue="BUG-111", outwardIssue="BUG-222"
        )

        # Verify result
        expected_result = "✅ Successfully linked BUG-111 relates BUG-222"
        self.assertEqual(result, expected_result)

    def test_link_jira_issues_with_duplicate_type(self):
        """Test linking JIRA issues with 'duplicates' relationship."""
        # Setup mock JIRA instance
        mock_jira = Mock(spec=JIRA)
        mock_jira.create_issue_link.return_value = Mock()

        # Call function
        result = link_jira_issues(
            inward_issue="FEAT-50",
            outward_issue="FEAT-51",
            link_type="duplicates",
            jira_instance=mock_jira,
        )

        # Verify link was created
        mock_jira.create_issue_link.assert_called_once_with(
            type="duplicates", inwardIssue="FEAT-50", outwardIssue="FEAT-51"
        )

        # Verify result
        expected_result = "✅ Successfully linked FEAT-50 duplicates FEAT-51"
        self.assertEqual(result, expected_result)

    def test_link_jira_issues_real_world_example(self):
        """Test linking JIRA issues with real-world ORIONINIT keys."""
        # Setup mock JIRA instance
        mock_jira = Mock(spec=JIRA)
        mock_jira.create_issue_link.return_value = Mock()

        # Call function with real-world issue keys
        result = link_jira_issues(
            inward_issue="ORIONINIT-163931",
            outward_issue="ORIONINIT-163077",
            link_type="causes",
            jira_instance=mock_jira,
        )

        # Verify link was created
        mock_jira.create_issue_link.assert_called_once_with(
            type="causes", inwardIssue="ORIONINIT-163931", outwardIssue="ORIONINIT-163077"
        )

        # Verify result
        expected_result = "✅ Successfully linked ORIONINIT-163931 causes ORIONINIT-163077"
        self.assertEqual(result, expected_result)


class TestLinkJiraIssuesInput(unittest.TestCase):
    """Test cases for LinkJiraIssuesInput schema."""

    def test_input_model_creation(self):
        """Test creating LinkJiraIssuesInput with all fields."""
        input_data = LinkJiraIssuesInput(inward_issue="TEST-123", outward_issue="TEST-456", link_type="blocks")

        self.assertEqual(input_data.inward_issue, "TEST-123")
        self.assertEqual(input_data.outward_issue, "TEST-456")
        self.assertEqual(input_data.link_type, "blocks")

    def test_input_model_default_link_type(self):
        """Test that link_type defaults to 'relates'."""
        input_data = LinkJiraIssuesInput(inward_issue="TEST-111", outward_issue="TEST-222")

        self.assertEqual(input_data.inward_issue, "TEST-111")
        self.assertEqual(input_data.outward_issue, "TEST-222")
        self.assertEqual(input_data.link_type, "relates")


if __name__ == "__main__":
    unittest.main()
