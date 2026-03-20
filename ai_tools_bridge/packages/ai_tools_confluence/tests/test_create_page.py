"""Tests for Confluence page creation functionality.

This module contains tests for creating new Confluence pages in spaces,
including success cases, error handling, and parent page relationships.
"""

import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from ai_tools_confluence.create_page import (
    CreateConfluencePageInput,
    create_confluence_page,
)


class TestCreateConfluencePageInput(unittest.TestCase):
    """Test cases for the CreateConfluencePageInput Pydantic model.

    Tests validation of input parameters for page creation.
    """

    def test_valid_input_with_all_fields(self):
        """Test that model accepts valid input with all fields."""
        input_data = CreateConfluencePageInput(
            space_key="PROJ",
            title="New Page",
            content="<p>Page content</p>",
            parent_id="123456",
        )
        self.assertEqual(input_data.space_key, "PROJ")
        self.assertEqual(input_data.title, "New Page")
        self.assertEqual(input_data.content, "<p>Page content</p>")
        self.assertEqual(input_data.parent_id, "123456")

    def test_valid_input_without_parent(self):
        """Test that model accepts valid input without optional parent_id."""
        input_data = CreateConfluencePageInput(
            space_key="PROJ",
            title="New Page",
            content="<p>Page content</p>",
        )
        self.assertEqual(input_data.space_key, "PROJ")
        self.assertEqual(input_data.title, "New Page")
        self.assertEqual(input_data.content, "<p>Page content</p>")
        self.assertIsNone(input_data.parent_id)

    def test_missing_space_key_raises_validation_error(self):
        """Test that missing space_key raises ValidationError."""
        with self.assertRaises(ValidationError):
            CreateConfluencePageInput(
                title="New Page",
                content="<p>Content</p>",
            )

    def test_missing_title_raises_validation_error(self):
        """Test that missing title raises ValidationError."""
        with self.assertRaises(ValidationError):
            CreateConfluencePageInput(
                space_key="PROJ",
                content="<p>Content</p>",
            )

    def test_missing_content_raises_validation_error(self):
        """Test that missing content raises ValidationError."""
        with self.assertRaises(ValidationError):
            CreateConfluencePageInput(
                space_key="PROJ",
                title="New Page",
            )


class TestCreateConfluencePage(unittest.TestCase):
    """Test cases for creating Confluence pages.

    Tests the create_confluence_page function with various scenarios.
    """

    def test_create_page_success_without_parent(self):
        """Test successful page creation without parent."""
        # Setup mock Confluence instance
        mock_confluence = Mock()
        mock_confluence.url = "https://confluence.example.com"
        mock_confluence.create_page.return_value = {
            "id": "789012",
            "title": "New Documentation Page",
        }

        # Call function
        result = create_confluence_page(
            space_key="PROJ",
            title="New Documentation Page",
            content="<p>This is the initial content</p>",
            confluence=mock_confluence,
        )

        # Verify create_page was called with correct parameters
        mock_confluence.create_page.assert_called_once_with(
            space="PROJ",
            title="New Documentation Page",
            body="<p>This is the initial content</p>",
            parent_id=None,
        )

        # Verify result message
        self.assertIn("Successfully created", result)
        self.assertIn("New Documentation Page", result)
        self.assertIn("789012", result)
        self.assertIn("PROJ", result)
        self.assertIn("https://confluence.example.com/pages/viewpage.action?pageId=789012", result)

    def test_create_page_success_with_parent(self):
        """Test successful page creation with parent page."""
        # Setup mock Confluence instance
        mock_confluence = Mock()
        mock_confluence.url = "https://confluence.example.com/"
        mock_confluence.create_page.return_value = {
            "id": "789013",
            "title": "Child Page",
        }

        # Call function with parent_id
        result = create_confluence_page(
            space_key="PROJ",
            title="Child Page",
            content="<p>Child content</p>",
            parent_id="123456",
            confluence=mock_confluence,
        )

        # Verify create_page was called with parent_id
        mock_confluence.create_page.assert_called_once_with(
            space="PROJ",
            title="Child Page",
            body="<p>Child content</p>",
            parent_id="123456",
        )

        # Verify result message mentions parent
        self.assertIn("Successfully created", result)
        self.assertIn("Child Page", result)
        self.assertIn("as child of parent '123456'", result)

    def test_create_page_api_returns_none(self):
        """Test error handling when API returns no result."""
        # Setup mock Confluence instance that returns None
        mock_confluence = Mock()
        mock_confluence.create_page.return_value = None

        # Verify ValueError is raised
        with self.assertRaises(ValueError) as context:
            create_confluence_page(
                space_key="PROJ",
                title="New Page",
                content="<p>Content</p>",
                confluence=mock_confluence,
            )

        self.assertIn("Page creation returned no result", str(context.exception))

    def test_create_page_api_error(self):
        """Test error handling when API call fails."""
        # Setup mock Confluence instance that raises exception
        mock_confluence = Mock()
        mock_confluence.create_page.side_effect = Exception("Space not found")

        # Verify ValueError is raised with proper message
        with self.assertRaises(ValueError) as context:
            create_confluence_page(
                space_key="INVALID",
                title="New Page",
                content="<p>Content</p>",
                confluence=mock_confluence,
            )

        self.assertIn("Failed to create", str(context.exception))
        self.assertIn("INVALID", str(context.exception))
        self.assertIn("Space not found", str(context.exception))

    def test_create_page_url_formatting(self):
        """Test that page URL is formatted correctly."""
        # Setup mock with URL with trailing slash
        mock_confluence = Mock()
        mock_confluence.url = "https://confluence.example.com/"
        mock_confluence.create_page.return_value = {
            "id": "999",
            "title": "Test",
        }

        # Call function
        result = create_confluence_page(
            space_key="TEST",
            title="Test",
            content="<p>Test</p>",
            confluence=mock_confluence,
        )

        # Verify URL doesn't have double slashes
        self.assertIn("https://confluence.example.com/pages/viewpage.action", result)
        self.assertNotIn("//pages", result)


if __name__ == "__main__":
    unittest.main()
