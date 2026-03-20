"""Tests for Confluence tool descriptions and integration.

This module tests the ToolDescription objects that wrap the Confluence functions
for use with AI frameworks like LangGraph and MCP.
"""

import unittest

from ai_tools_base import ToolDescription
from ai_tools_confluence.page import (
    GetConfluencePageByIdInput,
    GetConfluencePageByTitleInput,
    get_confluence_page_by_id,
    get_confluence_page_by_title,
)
from ai_tools_confluence.search import (
    ConfluenceCQLSearchInput,
    ConfluenceFreeTextSearchInput,
    search_confluence_pages_freetext,
    search_confluence_with_cql,
)
from ai_tools_confluence.tools import (
    tool_get_confluence_page_by_id,
    tool_get_confluence_page_by_title,
    tool_search_confluence_pages_freetext,
    tool_search_confluence_with_cql,
)


class TestToolGetConfluencePageById(unittest.TestCase):
    """Test cases for tool_get_confluence_page_by_id ToolDescription.

    Tests that the tool description is correctly configured for the page by ID function.
    """

    def test_is_tool_description_instance(self):
        """Test that tool is an instance of ToolDescription."""
        self.assertIsInstance(tool_get_confluence_page_by_id, ToolDescription)

    def test_tool_has_correct_function(self):
        """Test that tool wraps the correct function."""
        self.assertEqual(tool_get_confluence_page_by_id.func, get_confluence_page_by_id)

    def test_tool_has_correct_args_schema(self):
        """Test that tool uses the correct input schema."""
        self.assertEqual(tool_get_confluence_page_by_id.args_schema, GetConfluencePageByIdInput)

    def test_tool_name_is_set(self):
        """Test that tool has a name derived from function."""
        self.assertIsNotNone(tool_get_confluence_page_by_id.name)
        self.assertIsInstance(tool_get_confluence_page_by_id.name, str)

    def test_tool_description_is_set(self):
        """Test that tool has a description."""
        self.assertIsNotNone(tool_get_confluence_page_by_id.description)
        self.assertIsInstance(tool_get_confluence_page_by_id.description, str)


class TestToolGetConfluencePageByTitle(unittest.TestCase):
    """Test cases for tool_get_confluence_page_by_title ToolDescription.

    Tests that the tool description is correctly configured for the page by title function.
    """

    def test_is_tool_description_instance(self):
        """Test that tool is an instance of ToolDescription."""
        self.assertIsInstance(tool_get_confluence_page_by_title, ToolDescription)

    def test_tool_has_correct_function(self):
        """Test that tool wraps the correct function."""
        self.assertEqual(tool_get_confluence_page_by_title.func, get_confluence_page_by_title)

    def test_tool_has_correct_args_schema(self):
        """Test that tool uses the correct input schema."""
        self.assertEqual(tool_get_confluence_page_by_title.args_schema, GetConfluencePageByTitleInput)

    def test_tool_name_is_set(self):
        """Test that tool has a name derived from function."""
        self.assertIsNotNone(tool_get_confluence_page_by_title.name)
        self.assertIsInstance(tool_get_confluence_page_by_title.name, str)

    def test_tool_description_is_set(self):
        """Test that tool has a description."""
        self.assertIsNotNone(tool_get_confluence_page_by_title.description)
        self.assertIsInstance(tool_get_confluence_page_by_title.description, str)


class TestToolSearchConfluenceWithCQL(unittest.TestCase):
    """Test cases for tool_search_confluence_with_cql ToolDescription.

    Tests that the tool description is correctly configured for the CQL search function.
    """

    def test_is_tool_description_instance(self):
        """Test that tool is an instance of ToolDescription."""
        self.assertIsInstance(tool_search_confluence_with_cql, ToolDescription)

    def test_tool_has_correct_function(self):
        """Test that tool wraps the correct function."""
        self.assertEqual(tool_search_confluence_with_cql.func, search_confluence_with_cql)

    def test_tool_has_correct_args_schema(self):
        """Test that tool uses the correct input schema."""
        self.assertEqual(tool_search_confluence_with_cql.args_schema, ConfluenceCQLSearchInput)

    def test_tool_name_is_set(self):
        """Test that tool has a name derived from function."""
        self.assertIsNotNone(tool_search_confluence_with_cql.name)
        self.assertIsInstance(tool_search_confluence_with_cql.name, str)

    def test_tool_description_is_set(self):
        """Test that tool has a description."""
        self.assertIsNotNone(tool_search_confluence_with_cql.description)
        self.assertIsInstance(tool_search_confluence_with_cql.description, str)


class TestToolSearchConfluencePagesFreeText(unittest.TestCase):
    """Test cases for tool_search_confluence_pages_freetext ToolDescription."""

    def test_is_tool_description_instance(self):
        """Test that tool is an instance of ToolDescription."""
        self.assertIsInstance(tool_search_confluence_pages_freetext, ToolDescription)

    def test_tool_has_correct_function(self):
        """Test that tool wraps the free-text search function."""
        self.assertEqual(tool_search_confluence_pages_freetext.func, search_confluence_pages_freetext)

    def test_tool_has_correct_args_schema(self):
        """Test that tool uses the correct input schema."""
        self.assertEqual(
            tool_search_confluence_pages_freetext.args_schema,
            ConfluenceFreeTextSearchInput,
        )

    def test_tool_name_is_set(self):
        """Test that tool has a generated name."""
        self.assertIsNotNone(tool_search_confluence_pages_freetext.name)
        self.assertIsInstance(tool_search_confluence_pages_freetext.name, str)

    def test_tool_description_is_set(self):
        """Test that tool provides a description."""
        self.assertIsNotNone(tool_search_confluence_pages_freetext.description)
        self.assertIsInstance(tool_search_confluence_pages_freetext.description, str)


class TestToolsIntegration(unittest.TestCase):
    """Integration tests for all Confluence tools.

    Tests that all tools are properly exported and configured consistently.
    """

    def test_all_tools_are_unique(self):
        """Test that each tool is a distinct object."""
        tools = [
            tool_get_confluence_page_by_id,
            tool_get_confluence_page_by_title,
            tool_search_confluence_pages_freetext,
            tool_search_confluence_with_cql,
        ]
        self.assertEqual(len(tools), len(set(id(tool) for tool in tools)))

    def test_all_tools_have_unique_names(self):
        """Test that each tool has a unique name."""
        names = [
            tool_get_confluence_page_by_id.name,
            tool_get_confluence_page_by_title.name,
            tool_search_confluence_pages_freetext.name,
            tool_search_confluence_with_cql.name,
        ]
        self.assertEqual(len(names), len(set(names)))

    def test_all_tools_have_unique_functions(self):
        """Test that each tool wraps a different function."""
        functions = [
            tool_get_confluence_page_by_id.func,
            tool_get_confluence_page_by_title.func,
            tool_search_confluence_pages_freetext.func,
            tool_search_confluence_with_cql.func,
        ]
        self.assertEqual(len(functions), len(set(functions)))

    def test_all_tools_have_non_empty_descriptions(self):
        """Test that all tools have non-empty descriptions."""
        tools = [
            tool_get_confluence_page_by_id,
            tool_get_confluence_page_by_title,
            tool_search_confluence_pages_freetext,
            tool_search_confluence_with_cql,
        ]
        for tool in tools:
            with self.subTest(tool=tool.name):
                self.assertIsNotNone(tool.description)
                self.assertGreater(len(tool.description), 0)


if __name__ == "__main__":
    unittest.main()
