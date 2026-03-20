"""Tests for JIRA add comment functionality."""

import unittest
from unittest.mock import Mock

from jira import JIRA

from ai_tools_jira.add_comment import AddJiraCommentInput, add_jira_comment


class TestAddJiraComment(unittest.TestCase):
    """Test cases for adding comments to JIRA tickets."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_input = AddJiraCommentInput(
            issue_key="TEST-123",
            comment="This is a test comment",
        )

    def test_add_jira_comment_success(self):
        """Test successful JIRA comment addition."""
        # Setup mock JIRA instance
        mock_jira = Mock(spec=JIRA)
        mock_issue = Mock()
        mock_issue.key = "TEST-123"
        mock_jira.issue.return_value = mock_issue
        mock_jira.add_comment.return_value = Mock()

        # Call function
        result = add_jira_comment(
            issue_key=self.sample_input.issue_key,
            comment=self.sample_input.comment,
            jira_instance=mock_jira,
        )

        # Verify issue was retrieved
        mock_jira.issue.assert_called_once_with("TEST-123")

        # Verify comment was added
        mock_jira.add_comment.assert_called_once_with(mock_issue, "This is a test comment")

        # Verify result
        expected_result = "Comment added successfully to JIRA ticket TEST-123"
        self.assertEqual(result, expected_result)

    def test_add_jira_comment_with_empty_comment(self):
        """Test adding an empty comment to a JIRA ticket."""
        # Setup mock JIRA instance
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.key = "TEST-456"
        mock_jira.issue.return_value = mock_issue
        mock_jira.add_comment.return_value = Mock()

        # Call function with empty comment
        result = add_jira_comment(
            issue_key="TEST-456",
            comment="",
            jira_instance=mock_jira,
        )

        # Verify issue was retrieved
        mock_jira.issue.assert_called_once_with("TEST-456")

        # Verify comment was added (even if empty)
        mock_jira.add_comment.assert_called_once_with(mock_issue, "")

        # Verify result
        expected_result = "Comment added successfully to JIRA ticket TEST-456"
        self.assertEqual(result, expected_result)

    def test_add_jira_comment_with_multiline_comment(self):
        """Test adding a multiline comment to a JIRA ticket.

        Requirements:
        - The function should convert markdown formatting to JIRA wiki markup
        - Bullet lists (- item) should become JIRA bullets (* item)
        - Code blocks (```) should become JIRA code blocks ({code})
        """
        # Setup mock JIRA instance
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.key = "TEST-789"
        mock_jira.issue.return_value = mock_issue
        mock_jira.add_comment.return_value = Mock()

        multiline_comment = """This is a multiline comment.

        It contains multiple lines of text.
        
        Including some formatted content:
        - Item 1
        - Item 2
        
        And some code:
        ```python
        print("Hello, world!")
        ```
        """

        # Expected JIRA wiki markup format
        expected_jira_comment = """This is a multiline comment.

        It contains multiple lines of text.
        
        Including some formatted content:
*** Item 1
*** Item 2
        
        And some code:
{code}
        print("Hello, world!")
{code}
        """

        # Call function with multiline comment
        result = add_jira_comment(
            issue_key="TEST-789",
            comment=multiline_comment,
            jira_instance=mock_jira,
        )

        # Verify issue was retrieved
        mock_jira.issue.assert_called_once_with("TEST-789")

        # Verify comment was added with converted format
        mock_jira.add_comment.assert_called_once_with(mock_issue, expected_jira_comment)

        # Verify result
        expected_result = "Comment added successfully to JIRA ticket TEST-789"
        self.assertEqual(result, expected_result)

    def test_add_jira_comment_input_validation(self):
        """Test input validation for AddJiraCommentInput."""
        # Test valid input
        valid_input = AddJiraCommentInput(
            issue_key="PROJ-123",
            comment="Valid comment",
        )
        self.assertEqual(valid_input.issue_key, "PROJ-123")
        self.assertEqual(valid_input.comment, "Valid comment")

        # Test with different issue key formats
        test_cases = [
            ("ABC-1", "Simple comment"),
            ("PROJECT-9999", "Another comment"),
            ("X-1", "Short project key"),
        ]

        for issue_key, comment in test_cases:
            with self.subTest(issue_key=issue_key):
                input_obj = AddJiraCommentInput(
                    issue_key=issue_key,
                    comment=comment,
                )
                self.assertEqual(input_obj.issue_key, issue_key)
                self.assertEqual(input_obj.comment, comment)


if __name__ == "__main__":
    unittest.main()
