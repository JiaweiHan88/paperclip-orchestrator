"""Tests for Confluence comment functionality.

This module contains tests for adding comments to existing Confluence pages,
including success cases and error handling scenarios.
"""

import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from ai_tools_confluence.add_comment import (
    AddConfluenceCommentInput,
    add_confluence_comment,
)


class TestAddConfluenceCommentInput(unittest.TestCase):
    """Test cases for the AddConfluenceCommentInput Pydantic model.

    Tests validation of input parameters for adding comments.
    """

    def test_valid_input(self):
        """Test that model accepts valid input."""
        input_data = AddConfluenceCommentInput(
            page_id="123456",
            comment="<p>This is a comment</p>",
        )
        self.assertEqual(input_data.page_id, "123456")
        self.assertEqual(input_data.comment, "<p>This is a comment</p>")

    def test_valid_input_plain_text(self):
        """Test that model accepts plain text comments."""
        input_data = AddConfluenceCommentInput(
            page_id="123456",
            comment="Plain text comment",
        )
        self.assertEqual(input_data.page_id, "123456")
        self.assertEqual(input_data.comment, "Plain text comment")

    def test_missing_page_id_raises_validation_error(self):
        """Test that missing page_id raises ValidationError."""
        with self.assertRaises(ValidationError):
            AddConfluenceCommentInput(comment="A comment")

    def test_missing_comment_raises_validation_error(self):
        """Test that missing comment raises ValidationError."""
        with self.assertRaises(ValidationError):
            AddConfluenceCommentInput(page_id="123456")


class TestAddConfluenceComment(unittest.TestCase):
    """Test cases for adding comments to Confluence pages.

    Tests the add_confluence_comment function with various scenarios.
    """

    def test_add_comment_success(self):
        """Test successful comment addition."""
        # Setup mock Confluence instance
        mock_confluence = Mock()
        mock_confluence.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Project Documentation",
        }
        mock_confluence.add_comment.return_value = {
            "id": "comment-001",
        }

        # Call function
        result = add_confluence_comment(
            page_id="123456",
            comment="<p>Great documentation!</p>",
            confluence=mock_confluence,
        )

        # Verify get_page_by_id was called to verify page exists
        mock_confluence.get_page_by_id.assert_called_once_with(
            page_id="123456",
            expand="title",
        )

        # Verify add_comment was called with correct parameters
        mock_confluence.add_comment.assert_called_once_with(
            page_id="123456",
            text="<p>Great documentation!</p>",
        )

        # Verify result message
        self.assertIn("Successfully added comment", result)
        self.assertIn("comment-001", result)
        self.assertIn("Project Documentation", result)
        self.assertIn("123456", result)

    def test_add_comment_plain_text(self):
        """Test successful comment addition with plain text."""
        # Setup mock Confluence instance
        mock_confluence = Mock()
        mock_confluence.get_page_by_id.return_value = {
            "id": "789",
            "title": "Test Page",
        }
        mock_confluence.add_comment.return_value = {
            "id": "comment-002",
        }

        # Call function with plain text
        result = add_confluence_comment(
            page_id="789",
            comment="Simple plain text comment",
            confluence=mock_confluence,
        )

        # Verify add_comment was called with plain text
        mock_confluence.add_comment.assert_called_once_with(
            page_id="789",
            text="Simple plain text comment",
        )

        # Verify result message
        self.assertIn("Successfully added comment", result)

    def test_add_comment_page_not_found(self):
        """Test error handling when page is not found."""
        # Setup mock Confluence instance that returns None
        mock_confluence = Mock()
        mock_confluence.get_page_by_id.return_value = None

        # Verify ValueError is raised
        with self.assertRaises(ValueError) as context:
            add_confluence_comment(
                page_id="nonexistent",
                comment="<p>Comment</p>",
                confluence=mock_confluence,
            )

        self.assertIn("not found", str(context.exception))
        self.assertIn("nonexistent", str(context.exception))

    def test_add_comment_api_error_on_verification(self):
        """Test error handling when page verification fails."""
        # Setup mock Confluence instance that raises exception on get_page_by_id
        mock_confluence = Mock()
        mock_confluence.get_page_by_id.side_effect = Exception("Permission denied")

        # Verify ValueError is raised with proper message
        with self.assertRaises(ValueError) as context:
            add_confluence_comment(
                page_id="123456",
                comment="<p>Comment</p>",
                confluence=mock_confluence,
            )

        self.assertIn("Failed to add comment", str(context.exception))
        self.assertIn("Permission denied", str(context.exception))

    def test_add_comment_api_error_on_addition(self):
        """Test error handling when comment addition fails."""
        # Setup mock Confluence instance
        mock_confluence = Mock()
        mock_confluence.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Test Page",
        }
        mock_confluence.add_comment.side_effect = Exception("Comments disabled")

        # Verify ValueError is raised with proper message
        with self.assertRaises(ValueError) as context:
            add_confluence_comment(
                page_id="123456",
                comment="<p>Comment</p>",
                confluence=mock_confluence,
            )

        self.assertIn("Failed to add comment", str(context.exception))
        self.assertIn("Comments disabled", str(context.exception))

    def test_add_comment_returns_none(self):
        """Test error handling when add_comment returns None."""
        # Setup mock Confluence instance
        mock_confluence = Mock()
        mock_confluence.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Test Page",
        }
        mock_confluence.add_comment.return_value = None

        # Verify ValueError is raised
        with self.assertRaises(ValueError) as context:
            add_confluence_comment(
                page_id="123456",
                comment="<p>Comment</p>",
                confluence=mock_confluence,
            )

        self.assertIn("Comment addition returned no result", str(context.exception))


if __name__ == "__main__":
    unittest.main()
