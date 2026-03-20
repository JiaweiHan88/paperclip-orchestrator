"""Tests for Confluence page update functionality.

This module contains tests for updating existing Confluence pages,
including success cases and error handling scenarios.
"""

import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from ai_tools_confluence.update_page import (
    UpdateConfluencePageInput,
    update_confluence_page,
)


class TestUpdateConfluencePageInput(unittest.TestCase):
    """Test cases for the UpdateConfluencePageInput Pydantic model.

    Tests validation of input parameters for page updates.
    """

    def test_valid_input_with_all_fields(self):
        """Test that model accepts valid input with all fields."""
        input_data = UpdateConfluencePageInput(
            page_id="123456",
            content="<p>Updated content</p>",
            title="New Title",
        )
        self.assertEqual(input_data.page_id, "123456")
        self.assertEqual(input_data.content, "<p>Updated content</p>")
        self.assertEqual(input_data.title, "New Title")

    def test_valid_input_without_title(self):
        """Test that model accepts valid input without optional title."""
        input_data = UpdateConfluencePageInput(
            page_id="123456",
            content="<p>Updated content</p>",
        )
        self.assertEqual(input_data.page_id, "123456")
        self.assertEqual(input_data.content, "<p>Updated content</p>")
        self.assertIsNone(input_data.title)

    def test_missing_page_id_raises_validation_error(self):
        """Test that missing page_id raises ValidationError."""
        with self.assertRaises(ValidationError):
            UpdateConfluencePageInput(content="<p>Content</p>")

    def test_missing_content_raises_validation_error(self):
        """Test that missing content raises ValidationError."""
        with self.assertRaises(ValidationError):
            UpdateConfluencePageInput(page_id="123456")


class TestUpdateConfluencePage(unittest.TestCase):
    """Test cases for updating Confluence pages.

    Tests the update_confluence_page function with various scenarios.
    """

    def test_update_page_success_with_title(self):
        """Test successful page update with new title."""
        # Setup mock Confluence instance
        mock_confluence = Mock()
        mock_confluence.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Old Title",
            "version": {"number": 2},
        }
        mock_confluence.update_page.return_value = {
            "id": "123456",
            "title": "New Title",
            "version": {"number": 3},
        }

        # Call function
        result = update_confluence_page(
            page_id="123456",
            content="<p>Updated content</p>",
            title="New Title",
            confluence=mock_confluence,
        )

        # Verify get_page_by_id was called to fetch current version
        mock_confluence.get_page_by_id.assert_called_once_with(
            page_id="123456",
            expand="version",
        )

        # Verify update_page was called with correct parameters
        mock_confluence.update_page.assert_called_once_with(
            page_id="123456",
            title="New Title",
            body="<p>Updated content</p>",
        )

        # Verify result message
        self.assertIn("Successfully updated", result)
        self.assertIn("New Title", result)
        self.assertIn("123456", result)
        self.assertIn("version 3", result)

    def test_update_page_success_without_title(self):
        """Test successful page update without changing title."""
        # Setup mock Confluence instance
        mock_confluence = Mock()
        mock_confluence.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Existing Title",
            "version": {"number": 5},
        }
        mock_confluence.update_page.return_value = {
            "id": "123456",
            "title": "Existing Title",
            "version": {"number": 6},
        }

        # Call function without title parameter
        result = update_confluence_page(
            page_id="123456",
            content="<p>New content only</p>",
            confluence=mock_confluence,
        )

        # Verify update_page was called with existing title
        mock_confluence.update_page.assert_called_once_with(
            page_id="123456",
            title="Existing Title",
            body="<p>New content only</p>",
        )

        # Verify result message
        self.assertIn("Successfully updated", result)
        self.assertIn("Existing Title", result)

    def test_update_page_not_found(self):
        """Test error handling when page is not found."""
        # Setup mock Confluence instance that returns None
        mock_confluence = Mock()
        mock_confluence.get_page_by_id.return_value = None

        # Verify ValueError is raised
        with self.assertRaises(ValueError) as context:
            update_confluence_page(
                page_id="nonexistent",
                content="<p>Content</p>",
                confluence=mock_confluence,
            )

        self.assertIn("not found", str(context.exception))
        self.assertIn("nonexistent", str(context.exception))

    def test_update_page_api_error(self):
        """Test error handling when API call fails."""
        # Setup mock Confluence instance that raises exception
        mock_confluence = Mock()
        mock_confluence.get_page_by_id.side_effect = Exception("API Error")

        # Verify ValueError is raised with proper message
        with self.assertRaises(ValueError) as context:
            update_confluence_page(
                page_id="123456",
                content="<p>Content</p>",
                confluence=mock_confluence,
            )

        self.assertIn("Failed to update", str(context.exception))
        self.assertIn("API Error", str(context.exception))

    def test_update_page_increments_version(self):
        """Test that update_page is called correctly without manual version management."""
        # Setup mock with specific version
        mock_confluence = Mock()
        mock_confluence.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Title",
            "version": {"number": 10},
        }
        mock_confluence.update_page.return_value = {
            "id": "123456",
            "title": "Title",
            "version": {"number": 11},
        }

        # Call function
        update_confluence_page(
            page_id="123456",
            content="<p>Content</p>",
            confluence=mock_confluence,
        )

        # Verify update_page was called with correct parameters (no version_number)
        call_args = mock_confluence.update_page.call_args
        self.assertEqual(call_args[1]["page_id"], "123456")
        self.assertEqual(call_args[1]["body"], "<p>Content</p>")
        self.assertNotIn("version_number", call_args[1])


if __name__ == "__main__":
    unittest.main()
