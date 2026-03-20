"""Tests for Confluence CQL search functionality.

This module contains comprehensive tests for searching Confluence content using CQL queries,
including success cases, error handling, and edge cases.
"""

import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from ai_tools_confluence.search import (
    ConfluenceCQLSearchInput,
    ConfluenceFreeTextSearchInput,
    search_confluence_pages_freetext,
    search_confluence_with_cql,
)


class TestConfluenceCQLSearchInput(unittest.TestCase):
    """Test cases for the ConfluenceCQLSearchInput Pydantic model.

    Tests validation of input parameters for CQL search.
    """

    def test_valid_input_with_text_query(self):
        """Test that model accepts valid CQL text query."""
        input_data = ConfluenceCQLSearchInput(cql_query='text ~ "IPNEXT lifecycle" AND type=page')
        self.assertEqual(input_data.cql_query, 'text ~ "IPNEXT lifecycle" AND type=page')
        self.assertEqual(input_data.limit, 25)  # default value

    def test_valid_input_with_space_query(self):
        """Test that model accepts valid CQL space query."""
        input_data = ConfluenceCQLSearchInput(cql_query="type=blogpost AND space=BMWOSS", limit=50)
        self.assertEqual(input_data.cql_query, "type=blogpost AND space=BMWOSS")
        self.assertEqual(input_data.limit, 50)

    def test_valid_input_with_custom_limit(self):
        """Test that model accepts custom limit values."""
        input_data = ConfluenceCQLSearchInput(cql_query="type=page", limit=100)
        self.assertEqual(input_data.limit, 100)

    def test_default_limit_value(self):
        """Test that default limit is 25 when not specified."""
        input_data = ConfluenceCQLSearchInput(cql_query="type=page")
        self.assertEqual(input_data.limit, 25)

    def test_empty_query_accepted(self):
        """Test that empty CQL query is accepted (no explicit validation)."""
        input_data = ConfluenceCQLSearchInput(cql_query="")
        self.assertEqual(input_data.cql_query, "")

    def test_missing_cql_query_raises_validation_error(self):
        """Test that missing cql_query raises ValidationError."""
        with self.assertRaises(ValidationError):
            ConfluenceCQLSearchInput(limit=25)

    def test_complex_cql_query(self):
        """Test that complex CQL queries are accepted."""
        complex_query = 'text ~ "test" AND type=page AND space in (DEV, PROD) AND created >= "2024-01-01"'
        input_data = ConfluenceCQLSearchInput(cql_query=complex_query, limit=10)
        self.assertEqual(input_data.cql_query, complex_query)

    def test_limit_zero(self):
        """Test that limit of 0 is accepted."""
        input_data = ConfluenceCQLSearchInput(cql_query="type=page", limit=0)
        self.assertEqual(input_data.limit, 0)

    def test_negative_limit(self):
        """Test that negative limit is accepted (API will handle validation)."""
        input_data = ConfluenceCQLSearchInput(cql_query="type=page", limit=-1)
        self.assertEqual(input_data.limit, -1)


class TestConfluenceFreeTextSearchInput(unittest.TestCase):
    """Test cases for the ConfluenceFreeTextSearchInput Pydantic model."""

    def test_valid_input_defaults(self):
        """Test that model accepts a simple query with default values."""
        input_data = ConfluenceFreeTextSearchInput(text="release notes")
        self.assertEqual(input_data.text, "release notes")
        self.assertIsNone(input_data.space_keys)
        self.assertEqual(input_data.limit, 25)

    def test_input_with_space_keys(self):
        """Test that space keys are accepted and stored correctly."""
        input_data = ConfluenceFreeTextSearchInput(text="CI", space_keys=["DEV", "PROD"], limit=10)
        self.assertEqual(input_data.space_keys, ["DEV", "PROD"])
        self.assertEqual(input_data.limit, 10)

    def test_missing_query_raises_validation_error(self):
        """Test that missing query raises a validation error."""
        with self.assertRaises(ValidationError):
            ConfluenceFreeTextSearchInput()  # type: ignore[call-arg]


class TestSearchConfluenceWithCQL(unittest.TestCase):
    """Test cases for the search_confluence_with_cql function.

    Tests successful search execution, result formatting, and edge cases
    using mocks to avoid actual API calls.
    """

    def setUp(self):
        """Set up test fixtures and common test data."""
        self.cql_query = 'text ~ "IPNEXT lifecycle" AND type=page'
        self.mock_confluence = Mock()

    def test_successful_search_with_results(self):
        """Test successful search with multiple results."""
        mock_results = {
            "results": [
                {"content": {"id": "123456", "title": "IPNEXT Lifecycle Overview"}},
                {"content": {"id": "789012", "title": "IPNEXT Lifecycle Best Practices"}},
                {"content": {"id": "345678", "title": "IPNEXT Lifecycle Documentation"}},
            ]
        }
        self.mock_confluence.cql.return_value = mock_results

        result = search_confluence_with_cql(cql_query=self.cql_query, confluence=self.mock_confluence, limit=25)

        # Verify API call
        self.mock_confluence.cql.assert_called_once_with(cql=self.cql_query, limit=25)

        # Verify output format
        self.assertIn('Search Results for "text ~ "IPNEXT lifecycle" AND type=page" (- ID: TITLE):', result)
        self.assertIn("- 123456: IPNEXT Lifecycle Overview", result)
        self.assertIn("- 789012: IPNEXT Lifecycle Best Practices", result)
        self.assertIn("- 345678: IPNEXT Lifecycle Documentation", result)

        # Verify line structure
        lines = result.split("\n")
        self.assertEqual(len(lines), 4)  # header + 3 results

    def test_search_with_empty_results(self):
        """Test search that returns no results."""
        mock_results = {"results": []}
        self.mock_confluence.cql.return_value = mock_results

        result = search_confluence_with_cql(cql_query=self.cql_query, confluence=self.mock_confluence)

        # Verify only header is present
        self.assertIn('Search Results for "text ~ "IPNEXT lifecycle" AND type=page" (- ID: TITLE):', result)
        lines = result.split("\n")
        self.assertEqual(len(lines), 1)  # only header

    def test_search_with_custom_limit(self):
        """Test search with custom limit parameter."""
        mock_results = {"results": [{"content": {"id": "111", "title": "Test Page"}}]}
        self.mock_confluence.cql.return_value = mock_results
        custom_limit = 50

        search_confluence_with_cql(cql_query=self.cql_query, confluence=self.mock_confluence, limit=custom_limit)

        # Verify limit is passed to API
        self.mock_confluence.cql.assert_called_once_with(cql=self.cql_query, limit=custom_limit)

    def test_search_with_special_characters_in_titles(self):
        """Test search results containing special characters in titles."""
        mock_results = {
            "results": [
                {"content": {"id": "001", "title": "Page: Testing & Development [2024]"}},
                {"content": {"id": "002", "title": "Guide: BMW's CI/CD Pipeline"}},
            ]
        }
        self.mock_confluence.cql.return_value = mock_results

        result = search_confluence_with_cql(cql_query=self.cql_query, confluence=self.mock_confluence)

        self.assertIn("- 001: Page: Testing & Development [2024]", result)
        self.assertIn("- 002: Guide: BMW's CI/CD Pipeline", result)

    def test_search_with_single_result(self):
        """Test search that returns exactly one result."""
        mock_results = {"results": [{"content": {"id": "999", "title": "Single Result Page"}}]}
        self.mock_confluence.cql.return_value = mock_results

        result = search_confluence_with_cql(cql_query="type=page", confluence=self.mock_confluence)

        lines = result.split("\n")
        self.assertEqual(len(lines), 2)  # header + 1 result
        self.assertIn("- 999: Single Result Page", result)

    def test_search_result_format_consistency(self):
        """Test that result format is consistent across different queries."""
        mock_results = {
            "results": [
                {"content": {"id": "123", "title": "First"}},
                {"content": {"id": "456", "title": "Second"}},
            ]
        }
        self.mock_confluence.cql.return_value = mock_results

        result = search_confluence_with_cql(cql_query="simple query", confluence=self.mock_confluence)

        # Each result line should follow the pattern "- ID: TITLE"
        lines = result.split("\n")[1:]  # skip header
        for line in lines:
            self.assertTrue(line.startswith("- "))
            self.assertIn(": ", line)

    def test_search_with_space_query(self):
        """Test search with space-specific query."""
        space_query = "type=blogpost AND space=BMWOSS"
        mock_results = {
            "results": [
                {"content": {"id": "111", "title": "Blog Post 1"}},
                {"content": {"id": "222", "title": "Blog Post 2"}},
            ]
        }
        self.mock_confluence.cql.return_value = mock_results

        result = search_confluence_with_cql(cql_query=space_query, confluence=self.mock_confluence, limit=10)

        self.mock_confluence.cql.assert_called_once_with(cql=space_query, limit=10)
        self.assertIn(f'Search Results for "{space_query}" (- ID: TITLE):', result)

    def test_search_preserves_query_in_header(self):
        """Test that the original query is preserved in the result header."""
        original_query = 'text ~ "specific search" AND creator="john.doe"'
        mock_results = {"results": []}
        self.mock_confluence.cql.return_value = mock_results

        result = search_confluence_with_cql(cql_query=original_query, confluence=self.mock_confluence)

        self.assertIn(f'Search Results for "{original_query}" (- ID: TITLE):', result)

    def test_search_with_missing_results_key(self):
        """Test handling when API response doesn't have results key."""
        mock_results = {}  # No "results" key
        self.mock_confluence.cql.return_value = mock_results

        result = search_confluence_with_cql(cql_query=self.cql_query, confluence=self.mock_confluence)

        # Should only have header, no results
        lines = result.split("\n")
        self.assertEqual(len(lines), 1)

    def test_search_with_unicode_characters(self):
        """Test search with Unicode characters in query and results."""
        unicode_query = 'text ~ "日本語 测试 тест"'
        mock_results = {
            "results": [
                {"content": {"id": "777", "title": "Page with 日本語"}},
                {"content": {"id": "888", "title": "Страница с текстом"}},
            ]
        }
        self.mock_confluence.cql.return_value = mock_results

        result = search_confluence_with_cql(cql_query=unicode_query, confluence=self.mock_confluence)

        self.assertIn("- 777: Page with 日本語", result)
        self.assertIn("- 888: Страница с текстом", result)

    def test_default_limit_parameter(self):
        """Test that default limit of 25 is used when not specified."""
        mock_results = {"results": []}
        self.mock_confluence.cql.return_value = mock_results

        search_confluence_with_cql(cql_query=self.cql_query, confluence=self.mock_confluence)

        # Verify default limit is 25
        call_args = self.mock_confluence.cql.call_args
        self.assertEqual(call_args.kwargs["limit"], 25)

    def test_search_with_limit_one(self):
        """Test search with limit set to 1."""
        mock_results = {"results": [{"content": {"id": "001", "title": "Only Result"}}]}
        self.mock_confluence.cql.return_value = mock_results

        result = search_confluence_with_cql(cql_query="type=page", confluence=self.mock_confluence, limit=1)

        self.mock_confluence.cql.assert_called_once_with(cql="type=page", limit=1)
        self.assertIn("- 001: Only Result", result)


class TestSearchConfluencePagesFreeText(unittest.TestCase):
    """Test cases for the search_confluence_pages_freetext function."""

    def setUp(self):
        """Set up common query and mock Confluence instance."""
        self.query = "release notes"
        self.mock_confluence = Mock()

    def test_successful_search_with_results(self):
        """Test that free-text search formats multiple results correctly."""
        mock_results = {
            "results": [
                {"content": {"id": "101", "title": "Release Notes Q1"}},
                {"content": {"id": "202", "title": "Release Notes Q2"}},
            ]
        }
        self.mock_confluence.cql.return_value = mock_results

        result = search_confluence_pages_freetext(text=self.query, confluence=self.mock_confluence, limit=5)

        call_args = self.mock_confluence.cql.call_args
        self.assertEqual(call_args.kwargs["cql"], 'text ~ "release notes" AND type=page')
        self.assertEqual(call_args.kwargs["limit"], 5)
        self.assertIn('Free text search results for "release notes" (- ID: TITLE):', result)
        self.assertIn("- 101: Release Notes Q1", result)
        self.assertIn("- 202: Release Notes Q2", result)

    def test_search_with_space_keys(self):
        """Test that provided space keys are added to the CQL query."""
        self.mock_confluence.cql.return_value = {"results": []}
        space_keys = ["DEV", " PROD ", ""]

        search_confluence_pages_freetext(text=self.query, confluence=self.mock_confluence, space_keys=space_keys)

        expected_cql = 'text ~ "release notes" AND type=page AND space in ("DEV", "PROD")'
        self.assertEqual(self.mock_confluence.cql.call_args.kwargs["cql"], expected_cql)

    def test_search_escapes_quotes_in_query(self):
        """Test that double quotes in the query are escaped in the CQL string."""
        self.mock_confluence.cql.return_value = {"results": []}

        search_confluence_pages_freetext(text='deployment "pipeline"', confluence=self.mock_confluence)

        expected_cql = 'text ~ "deployment \\"pipeline\\"" AND type=page'
        self.assertEqual(self.mock_confluence.cql.call_args.kwargs["cql"], expected_cql)

    def test_search_with_empty_results(self):
        """Test that empty search results return only the header."""
        self.mock_confluence.cql.return_value = {"results": []}

        result = search_confluence_pages_freetext(text=self.query, confluence=self.mock_confluence)

        lines = result.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'Free text search results for "release notes" (- ID: TITLE):')


if __name__ == "__main__":
    unittest.main()
