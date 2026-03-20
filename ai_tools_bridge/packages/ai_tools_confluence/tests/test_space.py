"""Tests for Confluence space functionality.

This module contains tests for retrieving and formatting Confluence spaces.
"""

import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from ai_tools_confluence.space import (
    GetConfluencePageTreeInput,
    GetConfluenceSpacesInput,
    get_confluence_page_tree,
    get_confluence_spaces,
)


class TestGetConfluenceSpacesInput(unittest.TestCase):
    """Test cases for the GetConfluenceSpacesInput Pydantic model.

    Tests validation of input parameters for getting Confluence spaces.
    """

    def test_valid_input_default_limit(self):
        """Test that model accepts valid input with default limit."""
        input_data = GetConfluenceSpacesInput()
        self.assertEqual(input_data.limit, 100)

    def test_valid_input_custom_limit(self):
        """Test that model accepts custom limit values."""
        input_data = GetConfluenceSpacesInput(limit=50)
        self.assertEqual(input_data.limit, 50)

    def test_limit_zero(self):
        """Test that limit of 0 is accepted."""
        input_data = GetConfluenceSpacesInput(limit=0)
        self.assertEqual(input_data.limit, 0)


class TestGetConfluenceSpaces(unittest.TestCase):
    """Test cases for get_confluence_spaces function.

    Tests the main function for retrieving and formatting Confluence spaces.
    """

    def test_successful_spaces_retrieval(self):
        """Test successful retrieval and formatting of Confluence spaces."""
        mock_confluence = Mock()
        mock_confluence.get_all_spaces.return_value = {
            "results": [
                {"key": "SPACE1", "name": "Space One", "description": {"plain": {"value": "This is the first space"}}},
                {"key": "SPACE2", "name": "Space Two", "description": {"plain": {"value": "This is the second space"}}},
            ]
        }

        result = get_confluence_spaces(confluence=mock_confluence, limit=100)

        # Verify the confluence method was called correctly
        mock_confluence.get_all_spaces.assert_called_once_with(
            start=0,
            limit=100,
            expand="description,icon,homepage",
        )

        # Verify markdown formatting
        self.assertIn("# Confluence Spaces", result)
        self.assertIn("## Space One", result)
        self.assertIn("## Space Two", result)
        self.assertIn("- **Key**: `SPACE1`", result)
        self.assertIn("- **Key**: `SPACE2`", result)
        self.assertIn("- **Description**: This is the first space", result)
        self.assertIn("- **Description**: This is the second space", result)

    def test_spaces_without_description(self):
        """Test handling of spaces without description."""
        mock_confluence = Mock()
        mock_confluence.get_all_spaces.return_value = {
            "results": [{"key": "SPACE1", "name": "Space One", "description": None}]
        }

        result = get_confluence_spaces(confluence=mock_confluence)

        self.assertIn("## Space One", result)
        self.assertIn("- **Key**: `SPACE1`", result)
        self.assertIn("- **Description**: No description", result)

    def test_spaces_with_empty_description(self):
        """Test handling of spaces with empty description."""
        mock_confluence = Mock()
        mock_confluence.get_all_spaces.return_value = {
            "results": [{"key": "SPACE1", "name": "Space One", "description": {"plain": {"value": "   "}}}]
        }

        result = get_confluence_spaces(confluence=mock_confluence)

        self.assertIn("## Space One", result)
        self.assertIn("- **Description**: No description", result)

    def test_spaces_with_missing_plain_description(self):
        """Test handling of spaces where description object exists but plain field is missing."""
        mock_confluence = Mock()
        mock_confluence.get_all_spaces.return_value = {
            "results": [{"key": "SPACE1", "name": "Space One", "description": {}}]
        }

        result = get_confluence_spaces(confluence=mock_confluence)

        self.assertIn("## Space One", result)
        self.assertIn("- **Description**: No description", result)

    def test_empty_results(self):
        """Test handling of empty results from API."""
        mock_confluence = Mock()
        mock_confluence.get_all_spaces.return_value = {"results": []}

        result = get_confluence_spaces(confluence=mock_confluence)

        self.assertIn("# Confluence Spaces", result)
        # Should only contain the header
        self.assertEqual(result.count("##"), 0)

    def test_spaces_with_missing_name(self):
        """Test handling of spaces with missing name field."""
        mock_confluence = Mock()
        mock_confluence.get_all_spaces.return_value = {
            "results": [{"key": "SPACE1", "description": {"plain": {"value": "Description"}}}]
        }

        result = get_confluence_spaces(confluence=mock_confluence)

        self.assertIn("## N/A", result)
        self.assertIn("- **Key**: `SPACE1`", result)

    def test_spaces_with_missing_key(self):
        """Test handling of spaces with missing key field."""
        mock_confluence = Mock()
        mock_confluence.get_all_spaces.return_value = {
            "results": [{"name": "Space One", "description": {"plain": {"value": "Description"}}}]
        }

        result = get_confluence_spaces(confluence=mock_confluence)

        self.assertIn("## Space One", result)
        self.assertIn("- **Key**: `N/A`", result)

    def test_custom_limit_parameter(self):
        """Test that custom limit parameter is passed correctly."""
        mock_confluence = Mock()
        mock_confluence.get_all_spaces.return_value = {"results": []}

        get_confluence_spaces(confluence=mock_confluence, limit=50)

        mock_confluence.get_all_spaces.assert_called_once_with(
            start=0,
            limit=50,
            expand="description,icon,homepage",
        )

    def test_multiple_spaces_formatting(self):
        """Test correct formatting with multiple spaces."""
        mock_confluence = Mock()
        mock_confluence.get_all_spaces.return_value = {
            "results": [
                {"key": f"SPACE{i}", "name": f"Space {i}", "description": {"plain": {"value": f"Description {i}"}}}
                for i in range(1, 4)
            ]
        }

        result = get_confluence_spaces(confluence=mock_confluence)

        # Verify all spaces are included
        for i in range(1, 4):
            self.assertIn(f"## Space {i}", result)
            self.assertIn(f"- **Key**: `SPACE{i}`", result)
            self.assertIn(f"- **Description**: Description {i}", result)


class TestGetConfluencePageTreeInput(unittest.TestCase):
    """Test cases for the GetConfluencePageTreeInput Pydantic model.

    Tests validation of input parameters for getting Confluence page tree.
    """

    def test_valid_input_with_space_key(self):
        """Test that model accepts valid input with required space_key."""
        input_data = GetConfluencePageTreeInput(space_key="TESTSPACE")
        self.assertEqual(input_data.space_key, "TESTSPACE")
        self.assertEqual(input_data.limit, 100)
        self.assertIsNone(input_data.root_page_id)

    def test_valid_input_with_root_page_id(self):
        """Test that model accepts optional root_page_id."""
        input_data = GetConfluencePageTreeInput(space_key="TESTSPACE", root_page_id="12345")
        self.assertEqual(input_data.space_key, "TESTSPACE")
        self.assertEqual(input_data.root_page_id, "12345")
        self.assertEqual(input_data.limit, 100)

    def test_valid_input_custom_limit(self):
        """Test that model accepts custom limit values."""
        input_data = GetConfluencePageTreeInput(space_key="TESTSPACE", limit=50)
        self.assertEqual(input_data.limit, 50)

    def test_missing_space_key_raises_validation_error(self):
        """Test that missing space_key raises ValidationError."""
        with self.assertRaises(ValidationError):
            GetConfluencePageTreeInput()


class TestGetConfluencePageTree(unittest.TestCase):
    """Test cases for get_confluence_page_tree function.

    Tests the main function for retrieving and formatting Confluence page tree.
    """

    def test_successful_page_tree_from_space(self):
        """Test successful retrieval and formatting of page tree from space."""
        mock_confluence = Mock()
        mock_confluence.get_all_pages_from_space.return_value = [
            {"id": "1", "title": "Root Page", "ancestors": []},
            {"id": "2", "title": "Child Page 1", "ancestors": [{"id": "1"}]},
            {"id": "3", "title": "Child Page 2", "ancestors": [{"id": "1"}]},
            {"id": "4", "title": "Grandchild Page", "ancestors": [{"id": "1"}, {"id": "2"}]},
        ]

        result = get_confluence_page_tree(space_key="TESTSPACE", confluence=mock_confluence)

        # Verify the confluence method was called correctly
        mock_confluence.get_all_pages_from_space.assert_called_once_with(
            space="TESTSPACE",
            start=0,
            limit=100,
            expand="ancestors,space",
        )

        # Verify markdown formatting with tree structure
        self.assertIn("# Page Tree for Space: TESTSPACE", result)
        self.assertIn("- 1: Root Page", result)
        self.assertIn("  - 2: Child Page 1", result)
        self.assertIn("  - 3: Child Page 2", result)
        self.assertIn("    - 4: Grandchild Page", result)

    def test_page_tree_with_root_page_id(self):
        """Test retrieval of page tree starting from specific root page."""
        mock_confluence = Mock()
        mock_confluence.get_child_pages.return_value = [
            {"id": "2", "title": "Child Page 1", "ancestors": [{"id": "1"}]},
            {"id": "3", "title": "Child Page 2", "ancestors": [{"id": "1"}]},
        ]

        result = get_confluence_page_tree(space_key="TESTSPACE", confluence=mock_confluence, root_page_id="1")

        # Verify the confluence method was called correctly
        mock_confluence.get_child_pages.assert_called_once_with(page_id="1")

        # Verify output includes children
        self.assertIn("# Page Tree for Space: TESTSPACE", result)
        self.assertIn("- 2: Child Page 1", result)
        self.assertIn("- 3: Child Page 2", result)

    def test_empty_page_tree(self):
        """Test handling of empty page tree."""
        mock_confluence = Mock()
        mock_confluence.get_all_pages_from_space.return_value = []

        result = get_confluence_page_tree(space_key="TESTSPACE", confluence=mock_confluence)

        self.assertIn("# Page Tree for Space: TESTSPACE", result)
        # Should only contain the header
        lines = result.strip().split("\n")
        self.assertEqual(len(lines), 1)  # Just the header

    def test_page_tree_custom_limit(self):
        """Test that custom limit parameter is passed correctly."""
        mock_confluence = Mock()
        mock_confluence.get_all_pages_from_space.return_value = []

        get_confluence_page_tree(space_key="TESTSPACE", confluence=mock_confluence, limit=50)

        mock_confluence.get_all_pages_from_space.assert_called_once_with(
            space="TESTSPACE",
            start=0,
            limit=50,
            expand="ancestors,space",
        )

    def test_page_without_title(self):
        """Test handling of pages without title."""
        mock_confluence = Mock()
        mock_confluence.get_all_pages_from_space.return_value = [
            {"id": "1", "ancestors": []},
        ]

        result = get_confluence_page_tree(space_key="TESTSPACE", confluence=mock_confluence)

        self.assertIn("- 1: Untitled", result)

    def test_complex_tree_structure(self):
        """Test formatting of complex multi-level tree."""
        mock_confluence = Mock()
        mock_confluence.get_all_pages_from_space.return_value = [
            {"id": "1", "title": "Root 1", "ancestors": []},
            {"id": "2", "title": "Root 2", "ancestors": []},
            {"id": "3", "title": "Child 1-1", "ancestors": [{"id": "1"}]},
            {"id": "4", "title": "Child 1-2", "ancestors": [{"id": "1"}]},
            {"id": "5", "title": "Child 2-1", "ancestors": [{"id": "2"}]},
            {"id": "6", "title": "Grandchild 1-1-1", "ancestors": [{"id": "1"}, {"id": "3"}]},
            {"id": "7", "title": "Great-grandchild", "ancestors": [{"id": "1"}, {"id": "3"}, {"id": "6"}]},
        ]

        result = get_confluence_page_tree(space_key="TESTSPACE", confluence=mock_confluence)

        # Verify all pages are included with correct indentation
        self.assertIn("- 1: Root 1", result)
        self.assertIn("- 2: Root 2", result)
        self.assertIn("  - 3: Child 1-1", result)
        self.assertIn("  - 4: Child 1-2", result)
        self.assertIn("  - 5: Child 2-1", result)
        self.assertIn("    - 6: Grandchild 1-1-1", result)
        self.assertIn("      - 7: Great-grandchild", result)

    def test_pages_sorted_in_tree(self):
        """Test that pages are sorted at each level for consistent output."""
        mock_confluence = Mock()
        mock_confluence.get_all_pages_from_space.return_value = [
            {"id": "3", "title": "Page C", "ancestors": []},
            {"id": "1", "title": "Page A", "ancestors": []},
            {"id": "2", "title": "Page B", "ancestors": []},
        ]

        result = get_confluence_page_tree(space_key="TESTSPACE", confluence=mock_confluence)

        # Find positions of each page in the result
        pos_1 = result.find("- 1: Page A")
        pos_2 = result.find("- 2: Page B")
        pos_3 = result.find("- 3: Page C")

        # Verify pages appear in sorted order
        self.assertLess(pos_1, pos_2)
        self.assertLess(pos_2, pos_3)

    def test_orphaned_pages_handling(self):
        """Test handling of pages with parent references that don't exist in result set."""
        mock_confluence = Mock()
        mock_confluence.get_all_pages_from_space.return_value = [
            {"id": "1", "title": "Root Page", "ancestors": []},
            {"id": "2", "title": "Orphaned Page", "ancestors": [{"id": "999"}]},  # Parent not in result
        ]

        result = get_confluence_page_tree(space_key="TESTSPACE", confluence=mock_confluence)

        # Both pages should appear at root level since parent doesn't exist in page_map
        self.assertIn("- 1: Root Page", result)
        self.assertIn("- 2: Orphaned Page", result)
        # Orphaned page should be at root level (no indentation beyond root)
        lines = result.split("\n")
        orphaned_line = [line for line in lines if "Orphaned Page" in line][0]
        self.assertTrue(orphaned_line.startswith("- 2:"))


if __name__ == "__main__":
    unittest.main()
