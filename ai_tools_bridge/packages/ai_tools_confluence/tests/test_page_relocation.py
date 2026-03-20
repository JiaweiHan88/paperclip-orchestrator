"""Tests for Confluence page relocation functionality.

This module contains comprehensive tests for relocating (moving and copying)
Confluence pages, including success cases, error handling, and edge cases.
"""

import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from ai_tools_confluence.page_relocation import (
    RelocateConfluencePageInput,
    relocate_confluence_page,
)
from ai_tools_confluence.tools import tool_relocate_confluence_page


class TestRelocateConfluencePageInput(unittest.TestCase):
    """Test cases for the RelocateConfluencePageInput Pydantic model.

    Tests validation of input parameters for relocating a Confluence page.
    """

    def test_valid_input_move_operation(self):
        """Test that model accepts valid move operation."""
        input_data = RelocateConfluencePageInput(page_id="123456", new_parent_id="789012", operation="move")
        self.assertEqual(input_data.page_id, "123456")
        self.assertEqual(input_data.new_parent_id, "789012")
        self.assertEqual(input_data.operation, "move")
        self.assertIsNone(input_data.new_title)

    def test_valid_input_copy_operation(self):
        """Test that model accepts valid copy operation."""
        input_data = RelocateConfluencePageInput(page_id="123456", new_parent_id="789012", operation="copy")
        self.assertEqual(input_data.page_id, "123456")
        self.assertEqual(input_data.new_parent_id, "789012")
        self.assertEqual(input_data.operation, "copy")
        self.assertIsNone(input_data.new_title)

    def test_default_operation_is_move(self):
        """Test that default operation is 'move'."""
        input_data = RelocateConfluencePageInput(page_id="123456", new_parent_id="789012")
        self.assertEqual(input_data.operation, "move")

    def test_valid_input_with_new_title(self):
        """Test that model accepts optional new_title parameter."""
        input_data = RelocateConfluencePageInput(
            page_id="123456", new_parent_id="789012", operation="copy", new_title="New Title"
        )
        self.assertEqual(input_data.new_title, "New Title")

    def test_missing_page_id_raises_validation_error(self):
        """Test that missing page_id raises ValidationError."""
        with self.assertRaises(ValidationError):
            RelocateConfluencePageInput(new_parent_id="789012")

    def test_missing_new_parent_id_raises_validation_error(self):
        """Test that missing new_parent_id raises ValidationError."""
        with self.assertRaises(ValidationError):
            RelocateConfluencePageInput(page_id="123456")


class TestRelocateConfluencePageMove(unittest.TestCase):
    """Test cases for the relocate_confluence_page function with move operation.

    Tests moving Confluence pages to different parent pages.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.mock_confluence = Mock()
        self.page_id = "123456"
        self.new_parent_id = "789012"
        self.page_title = "Test Page"
        self.parent_title = "Parent Page"

    def test_successful_page_move(self):
        """Test successful move of a Confluence page to new parent."""
        mock_page = {
            "id": self.page_id,
            "title": self.page_title,
            "version": {"number": 5},
            "body": {"storage": {"value": "<p>Test content</p>"}},
        }
        mock_parent = {
            "id": self.new_parent_id,
            "title": self.parent_title,
        }

        self.mock_confluence.get_page_by_id.side_effect = [mock_page, mock_parent]
        self.mock_confluence.update_page.return_value = {"id": self.page_id}

        result = relocate_confluence_page(
            page_id=self.page_id,
            new_parent_id=self.new_parent_id,
            confluence=self.mock_confluence,
            operation="move",
        )

        # Verify calls
        self.assertEqual(self.mock_confluence.get_page_by_id.call_count, 2)
        self.mock_confluence.get_page_by_id.assert_any_call(self.page_id, expand="body.storage,space,version")
        self.mock_confluence.get_page_by_id.assert_any_call(self.new_parent_id)
        self.mock_confluence.update_page.assert_called_once_with(
            parent_id=self.new_parent_id,
            page_id=self.page_id,
            title=self.page_title,
            body="<p>Test content</p>",
            always_update=True,
        )

        # Verify result
        self.assertIn(self.page_title, result)
        self.assertIn(self.page_id, result)
        self.assertIn(self.parent_title, result)
        self.assertIn(self.new_parent_id, result)
        self.assertIn("Successfully moved", result)

    def test_move_default_operation(self):
        """Test that move is the default operation."""
        mock_page = {
            "title": self.page_title,
            "version": {"number": 5},
            "body": {"storage": {"value": "<p>Test content</p>"}},
        }
        mock_parent = {"title": self.parent_title}

        self.mock_confluence.get_page_by_id.side_effect = [mock_page, mock_parent]
        self.mock_confluence.update_page.return_value = {"id": self.page_id}

        result = relocate_confluence_page(
            page_id=self.page_id,
            new_parent_id=self.new_parent_id,
            confluence=self.mock_confluence,
            # No operation specified - should default to "move"
        )

        # Should call update_page for move operation
        self.mock_confluence.update_page.assert_called_once()
        self.assertIn("Successfully moved", result)

    def test_move_fails_when_page_not_found(self):
        """Test that move raises ValueError when page is not found."""
        self.mock_confluence.get_page_by_id.side_effect = Exception("Page not found")

        with self.assertRaises(ValueError) as context:
            relocate_confluence_page(
                page_id=self.page_id,
                new_parent_id=self.new_parent_id,
                confluence=self.mock_confluence,
                operation="move",
            )

        self.assertIn(self.page_id, str(context.exception))
        self.assertIn(self.new_parent_id, str(context.exception))
        self.assertIn("Error moving page", str(context.exception))

    def test_move_fails_when_version_missing(self):
        """Test that move raises ValueError when page version is missing."""
        mock_page = {
            "id": self.page_id,
            "title": self.page_title,
            "body": {"storage": {"value": "<p>Test content</p>"}},
        }

        self.mock_confluence.get_page_by_id.return_value = mock_page

        with self.assertRaises(ValueError) as context:
            relocate_confluence_page(
                page_id=self.page_id,
                new_parent_id=self.new_parent_id,
                confluence=self.mock_confluence,
                operation="move",
            )

        self.assertIn("Could not determine version", str(context.exception))

    def test_move_fails_when_parent_not_found(self):
        """Test that move raises ValueError when parent page is not found."""
        mock_page = {
            "title": self.page_title,
            "version": {"number": 5},
            "body": {"storage": {"value": "<p>Test content</p>"}},
        }

        self.mock_confluence.get_page_by_id.side_effect = [
            mock_page,
            Exception("Parent not found"),
        ]

        with self.assertRaises(ValueError) as context:
            relocate_confluence_page(
                page_id=self.page_id,
                new_parent_id=self.new_parent_id,
                confluence=self.mock_confluence,
                operation="move",
            )

        self.assertIn(self.page_id, str(context.exception))
        self.assertIn(self.new_parent_id, str(context.exception))


class TestRelocateConfluencePageCopy(unittest.TestCase):
    """Test cases for the relocate_confluence_page function with copy operation.

    Tests copying Confluence pages to different parent pages.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.mock_confluence = Mock()
        self.page_id = "123456"
        self.new_parent_id = "789012"
        self.page_title = "Test Page"
        self.parent_title = "Parent Page"
        self.space_key = "TEST"

    def test_successful_page_copy_without_new_title(self):
        """Test successful copy of a Confluence page without new title."""
        mock_source_page = {
            "id": self.page_id,
            "title": self.page_title,
            "body": {"storage": {"value": "<p>Test content</p>"}},
            "space": {"key": self.space_key},
        }
        mock_parent = {
            "id": self.new_parent_id,
            "title": self.parent_title,
        }
        mock_new_page = {
            "id": "999999",
            "title": f"{self.page_title} (Copy)",
        }

        self.mock_confluence.get_page_by_id.side_effect = [mock_source_page, mock_parent]
        self.mock_confluence.create_page.return_value = mock_new_page

        result = relocate_confluence_page(
            page_id=self.page_id,
            new_parent_id=self.new_parent_id,
            confluence=self.mock_confluence,
            operation="copy",
        )

        # Verify calls
        self.assertEqual(self.mock_confluence.get_page_by_id.call_count, 2)
        self.mock_confluence.get_page_by_id.assert_any_call(self.page_id, expand="body.storage,space")
        self.mock_confluence.get_page_by_id.assert_any_call(self.new_parent_id)
        self.mock_confluence.create_page.assert_called_once_with(
            space=self.space_key,
            title=f"{self.page_title} (Copy)",
            body="<p>Test content</p>",
            parent_id=self.new_parent_id,
        )

        # Verify result
        self.assertIn(self.page_title, result)
        self.assertIn("(Copy)", result)
        self.assertIn("999999", result)
        self.assertIn(self.parent_title, result)
        self.assertIn(self.new_parent_id, result)
        self.assertIn("Successfully copied", result)

    def test_successful_page_copy_with_new_title(self):
        """Test successful copy of a Confluence page with custom new title."""
        new_title = "Custom Title"
        mock_source_page = {
            "title": self.page_title,
            "body": {"storage": {"value": "<p>Test content</p>"}},
            "space": {"key": self.space_key},
        }
        mock_parent = {"title": self.parent_title}
        mock_new_page = {"id": "999999", "title": new_title}

        self.mock_confluence.get_page_by_id.side_effect = [mock_source_page, mock_parent]
        self.mock_confluence.create_page.return_value = mock_new_page

        result = relocate_confluence_page(
            page_id=self.page_id,
            new_parent_id=self.new_parent_id,
            confluence=self.mock_confluence,
            operation="copy",
            new_title=new_title,
        )

        # Verify create_page called with custom title
        self.mock_confluence.create_page.assert_called_once_with(
            space=self.space_key,
            title=new_title,
            body="<p>Test content</p>",
            parent_id=self.new_parent_id,
        )

        # Verify result
        self.assertIn(new_title, result)
        self.assertIn("999999", result)

    def test_copy_fails_when_source_page_not_found(self):
        """Test that copy raises ValueError when source page is not found."""
        self.mock_confluence.get_page_by_id.side_effect = Exception("Page not found")

        with self.assertRaises(ValueError) as context:
            relocate_confluence_page(
                page_id=self.page_id,
                new_parent_id=self.new_parent_id,
                confluence=self.mock_confluence,
                operation="copy",
            )

        self.assertIn(self.page_id, str(context.exception))
        self.assertIn(self.new_parent_id, str(context.exception))
        self.assertIn("Error copying page", str(context.exception))

    def test_copy_fails_when_space_key_missing(self):
        """Test that copy raises ValueError when space key is missing."""
        mock_source_page = {
            "title": self.page_title,
            "body": {"storage": {"value": "<p>Test content</p>"}},
            "space": {},
        }

        self.mock_confluence.get_page_by_id.return_value = mock_source_page

        with self.assertRaises(ValueError) as context:
            relocate_confluence_page(
                page_id=self.page_id,
                new_parent_id=self.new_parent_id,
                confluence=self.mock_confluence,
                operation="copy",
            )

        self.assertIn("Could not determine space key", str(context.exception))


class TestToolDescription(unittest.TestCase):
    """Test cases for tool description.

    Tests that the tool is properly configured with correct function and schema.
    """

    def test_tool_has_correct_function(self):
        """Test that relocate tool has correct function reference."""
        self.assertEqual(tool_relocate_confluence_page.func, relocate_confluence_page)

    def test_tool_has_correct_schema(self):
        """Test that relocate tool has correct schema reference."""
        self.assertEqual(tool_relocate_confluence_page.args_schema, RelocateConfluencePageInput)


if __name__ == "__main__":
    unittest.main()
