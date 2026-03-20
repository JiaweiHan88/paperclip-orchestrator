"""Tests for Confluence page retrieval and rendering functionality.

This module contains comprehensive tests for fetching and rendering Confluence pages,
including success cases, error handling, and edge cases for both ID and title-based lookups.
"""

import unittest
from unittest.mock import Mock, patch

from pydantic import ValidationError

from ai_tools_confluence.page import (
    GetConfluencePageByIdHtmlInput,
    GetConfluencePageByIdInput,
    GetConfluencePageByTitleHtmlInput,
    GetConfluencePageByTitleInput,
    extract_html_content,
    get_confluence_page_by_id,
    get_confluence_page_by_id_html,
    get_confluence_page_by_title,
    get_confluence_page_by_title_html,
    render_page_to_markdown,
)


class TestGetConfluencePageByIdInput(unittest.TestCase):
    """Test cases for the GetConfluencePageByIdInput Pydantic model.

    Tests validation of input parameters for page retrieval by ID.
    """

    def test_valid_input_with_numeric_id(self):
        """Test that model accepts valid numeric page ID."""
        input_data = GetConfluencePageByIdInput(id="123456")
        self.assertEqual(input_data.id, "123456")

    def test_valid_input_with_alphanumeric_id(self):
        """Test that model accepts valid alphanumeric page ID."""
        input_data = GetConfluencePageByIdInput(id="abc123def")
        self.assertEqual(input_data.id, "abc123def")

    def test_empty_id_accepted(self):
        """Test that empty ID is accepted (no explicit validation)."""
        input_data = GetConfluencePageByIdInput(id="")
        self.assertEqual(input_data.id, "")

    def test_missing_id_raises_validation_error(self):
        """Test that missing ID raises ValidationError."""
        with self.assertRaises(ValidationError):
            GetConfluencePageByIdInput()


class TestGetConfluencePageByTitleInput(unittest.TestCase):
    """Test cases for the GetConfluencePageByTitleInput Pydantic model.

    Tests validation of input parameters for page retrieval by title and space.
    """

    def test_valid_input_with_title_and_space(self):
        """Test that model accepts valid title and space key."""
        input_data = GetConfluencePageByTitleInput(title="My Page", space_key="MYSPACE")
        self.assertEqual(input_data.title, "My Page")
        self.assertEqual(input_data.space_key, "MYSPACE")

    def test_valid_input_with_special_characters_in_title(self):
        """Test that model accepts title with special characters."""
        input_data = GetConfluencePageByTitleInput(title="Page: Testing & Development", space_key="DEV")
        self.assertEqual(input_data.title, "Page: Testing & Development")

    def test_missing_title_raises_validation_error(self):
        """Test that missing title raises ValidationError."""
        with self.assertRaises(ValidationError):
            GetConfluencePageByTitleInput(space_key="MYSPACE")

    def test_missing_space_key_raises_validation_error(self):
        """Test that missing space_key raises ValidationError."""
        with self.assertRaises(ValidationError):
            GetConfluencePageByTitleInput(title="My Page")

    def test_empty_strings_accepted(self):
        """Test that empty strings for title and space_key are accepted."""
        input_data = GetConfluencePageByTitleInput(title="", space_key="")
        self.assertEqual(input_data.title, "")
        self.assertEqual(input_data.space_key, "")


class TestRenderPageToMarkdown(unittest.TestCase):
    """Test cases for the render_page_to_markdown function.

    Tests markdown rendering logic with various page structures and error cases.
    """

    @patch("ai_tools_confluence.page.convert_to_markdown")
    def test_successful_rendering_with_valid_page(self, mock_convert):
        """Test successful rendering of a valid Confluence page."""
        mock_convert.return_value = "# Rendered Markdown Content"

        page = {"body": {"storage": {"value": "<h1>HTML Content</h1>"}}}

        result = render_page_to_markdown(page)

        mock_convert.assert_called_once_with("<h1>HTML Content</h1>")
        self.assertEqual(result, "# Rendered Markdown Content")

    def test_none_page_raises_value_error(self):
        """Test that None page raises ValueError with appropriate message."""
        with self.assertRaises(ValueError) as context:
            render_page_to_markdown(None)

        self.assertIn("Page with not found", str(context.exception))

    def test_missing_body_raises_value_error(self):
        """Test that page without body raises ValueError."""
        page = {"title": "Test Page"}

        with self.assertRaises(ValueError) as context:
            render_page_to_markdown(page)

        self.assertIn("no body content", str(context.exception))

    def test_missing_storage_raises_value_error(self):
        """Test that page body without storage raises ValueError."""
        page = {"body": {"view": {"value": "some content"}}}

        with self.assertRaises(ValueError) as context:
            render_page_to_markdown(page)

        self.assertIn("no storage content", str(context.exception))

    def test_missing_value_raises_value_error(self):
        """Test that storage without value raises ValueError."""
        page = {"body": {"storage": {"representation": "storage"}}}

        with self.assertRaises(ValueError) as context:
            render_page_to_markdown(page)

        self.assertIn("no HTML value", str(context.exception))

    @patch("ai_tools_confluence.page.convert_to_markdown")
    def test_rendering_with_empty_html_content(self, mock_convert):
        """Test rendering when HTML content is empty string."""
        mock_convert.return_value = ""

        page = {"body": {"storage": {"value": ""}}}

        result = render_page_to_markdown(page)

        mock_convert.assert_called_once_with("")
        self.assertEqual(result, "")

    @patch("ai_tools_confluence.page.convert_to_markdown")
    def test_rendering_with_complex_html(self, mock_convert):
        """Test rendering with complex HTML structure."""
        complex_html = """
        <h1>Title</h1>
        <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        """
        expected_markdown = "# Title\n\nParagraph with **bold** and *italic* text.\n\n- Item 1\n- Item 2"
        mock_convert.return_value = expected_markdown

        page = {"body": {"storage": {"value": complex_html}}}

        result = render_page_to_markdown(page)

        mock_convert.assert_called_once_with(complex_html)
        self.assertEqual(result, expected_markdown)


class TestGetConfluencePageById(unittest.TestCase):
    """Test cases for the get_confluence_page_by_id function.

    Tests successful page retrieval by ID, error conditions, and markdown conversion.
    """

    def setUp(self):
        """Set up test fixtures and common test data."""
        self.page_id = "123456"
        self.mock_confluence = Mock()

    @patch("ai_tools_confluence.page.render_page_to_markdown")
    def test_successful_page_retrieval_by_id(self, mock_render):
        """Test successful retrieval and rendering of page by ID."""
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_id.return_value = mock_page
        mock_render.return_value = "# Test"

        result = get_confluence_page_by_id(id=self.page_id, confluence=self.mock_confluence)

        self.mock_confluence.get_page_by_id.assert_called_once_with(self.page_id, expand="body.storage")
        mock_render.assert_called_once_with(mock_page)
        self.assertEqual(result, "# Test")

    @patch("ai_tools_confluence.page.render_page_to_markdown")
    def test_api_returns_page_with_all_fields(self, mock_render):
        """Test handling of page with all available fields."""
        mock_page = {
            "id": "123456",
            "title": "Test Page",
            "body": {"storage": {"value": "<h1>Content</h1>"}},
            "version": {"number": 5},
        }
        self.mock_confluence.get_page_by_id.return_value = mock_page
        mock_render.return_value = "# Content"

        result = get_confluence_page_by_id(id=self.page_id, confluence=self.mock_confluence)

        self.assertEqual(result, "# Content")

    @patch("ai_tools_confluence.page.render_page_to_markdown")
    def test_rendering_error_raises_value_error(self, mock_render):
        """Test that rendering errors are caught and wrapped in ValueError."""
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_id.return_value = mock_page
        mock_render.side_effect = ValueError("Missing body content")

        with self.assertRaises(ValueError) as context:
            get_confluence_page_by_id(id=self.page_id, confluence=self.mock_confluence)

        self.assertIn("Error rendering page with ID", str(context.exception))
        self.assertIn(self.page_id, str(context.exception))

    @patch("ai_tools_confluence.page.render_page_to_markdown")
    def test_generic_exception_during_rendering(self, mock_render):
        """Test handling of unexpected exceptions during rendering."""
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_id.return_value = mock_page
        mock_render.side_effect = Exception("Unexpected error")

        with self.assertRaises(ValueError) as context:
            get_confluence_page_by_id(id=self.page_id, confluence=self.mock_confluence)

        self.assertIn("Error rendering page with ID", str(context.exception))
        self.assertIn("Unexpected error", str(context.exception))


class TestGetConfluencePageByTitle(unittest.TestCase):
    """Test cases for the get_confluence_page_by_title function.

    Tests successful page retrieval by title and space, error conditions, and markdown conversion.
    """

    def setUp(self):
        """Set up test fixtures and common test data."""
        self.title = "My Test Page"
        self.space_key = "TESTSPACE"
        self.mock_confluence = Mock()

    @patch("ai_tools_confluence.page.render_page_to_markdown")
    def test_successful_page_retrieval_by_title(self, mock_render):
        """Test successful retrieval and rendering of page by title."""
        mock_page = {"body": {"storage": {"value": "<p>Content</p>"}}}
        self.mock_confluence.get_page_by_title.return_value = mock_page
        mock_render.return_value = "Content"

        result = get_confluence_page_by_title(
            title=self.title, space_key=self.space_key, confluence=self.mock_confluence
        )

        self.mock_confluence.get_page_by_title.assert_called_once_with(
            self.space_key, self.title, expand="body.storage"
        )
        mock_render.assert_called_once_with(mock_page)
        self.assertEqual(result, "Content")

    @patch("ai_tools_confluence.page.render_page_to_markdown")
    def test_page_with_special_characters_in_title(self, mock_render):
        """Test retrieval of page with special characters in title."""
        special_title = "Page: Testing & Development [2024]"
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_title.return_value = mock_page
        mock_render.return_value = "# Test"

        result = get_confluence_page_by_title(
            title=special_title, space_key=self.space_key, confluence=self.mock_confluence
        )

        self.mock_confluence.get_page_by_title.assert_called_once_with(
            self.space_key, special_title, expand="body.storage"
        )
        self.assertEqual(result, "# Test")

    @patch("ai_tools_confluence.page.render_page_to_markdown")
    def test_rendering_error_raises_value_error_with_title(self, mock_render):
        """Test that rendering errors include the page title in error message."""
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_title.return_value = mock_page
        mock_render.side_effect = ValueError("Missing storage content")

        with self.assertRaises(ValueError) as context:
            get_confluence_page_by_title(title=self.title, space_key=self.space_key, confluence=self.mock_confluence)

        self.assertIn("Error rendering page with title", str(context.exception))
        self.assertIn(self.title, str(context.exception))

    @patch("ai_tools_confluence.page.render_page_to_markdown")
    def test_generic_exception_during_rendering_by_title(self, mock_render):
        """Test handling of unexpected exceptions during rendering by title."""
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_title.return_value = mock_page
        mock_render.side_effect = RuntimeError("Rendering failed")

        with self.assertRaises(ValueError) as context:
            get_confluence_page_by_title(title=self.title, space_key=self.space_key, confluence=self.mock_confluence)

        self.assertIn("Error rendering page with title", str(context.exception))
        self.assertIn("Rendering failed", str(context.exception))


class TestGetConfluencePageByIdHtmlInput(unittest.TestCase):
    """Test cases for the GetConfluencePageByIdHtmlInput Pydantic model.

    Tests validation of input parameters for HTML page retrieval by ID.
    """

    def test_valid_input_with_numeric_id(self):
        """Test that model accepts valid numeric page ID."""
        input_data = GetConfluencePageByIdHtmlInput(id="123456")
        self.assertEqual(input_data.id, "123456")

    def test_valid_input_with_alphanumeric_id(self):
        """Test that model accepts valid alphanumeric page ID."""
        input_data = GetConfluencePageByIdHtmlInput(id="abc123def")
        self.assertEqual(input_data.id, "abc123def")

    def test_empty_id_accepted(self):
        """Test that empty ID is accepted (no explicit validation)."""
        input_data = GetConfluencePageByIdHtmlInput(id="")
        self.assertEqual(input_data.id, "")

    def test_missing_id_raises_validation_error(self):
        """Test that missing ID raises ValidationError."""
        with self.assertRaises(ValidationError):
            GetConfluencePageByIdHtmlInput()


class TestGetConfluencePageByTitleHtmlInput(unittest.TestCase):
    """Test cases for the GetConfluencePageByTitleHtmlInput Pydantic model.

    Tests validation of input parameters for HTML page retrieval by title and space.
    """

    def test_valid_input_with_title_and_space(self):
        """Test that model accepts valid title and space key."""
        input_data = GetConfluencePageByTitleHtmlInput(title="My Page", space_key="MYSPACE")
        self.assertEqual(input_data.title, "My Page")
        self.assertEqual(input_data.space_key, "MYSPACE")

    def test_valid_input_with_special_characters_in_title(self):
        """Test that model accepts title with special characters."""
        input_data = GetConfluencePageByTitleHtmlInput(title="Page: Testing & Development", space_key="DEV")
        self.assertEqual(input_data.title, "Page: Testing & Development")

    def test_missing_title_raises_validation_error(self):
        """Test that missing title raises ValidationError."""
        with self.assertRaises(ValidationError):
            GetConfluencePageByTitleHtmlInput(space_key="MYSPACE")

    def test_missing_space_key_raises_validation_error(self):
        """Test that missing space_key raises ValidationError."""
        with self.assertRaises(ValidationError):
            GetConfluencePageByTitleHtmlInput(title="My Page")

    def test_empty_strings_accepted(self):
        """Test that empty strings for title and space_key are accepted."""
        input_data = GetConfluencePageByTitleHtmlInput(title="", space_key="")
        self.assertEqual(input_data.title, "")
        self.assertEqual(input_data.space_key, "")


class TestExtractHtmlContent(unittest.TestCase):
    """Test cases for the extract_html_content function.

    Tests HTML extraction logic with various page structures and error cases.
    """

    def test_successful_extraction_with_valid_page(self):
        """Test successful extraction of HTML from a valid Confluence page."""
        page = {"body": {"storage": {"value": "<h1>HTML Content</h1><p>Paragraph</p>"}}}

        result = extract_html_content(page)

        self.assertEqual(result, "<h1>HTML Content</h1><p>Paragraph</p>")

    def test_none_page_raises_value_error(self):
        """Test that None page raises ValueError with descriptive message."""
        with self.assertRaises(ValueError) as context:
            extract_html_content(None)

        self.assertIn("Page with not found", str(context.exception))

    def test_page_without_body_raises_value_error(self):
        """Test that page without body raises ValueError."""
        page = {"title": "My Page"}

        with self.assertRaises(ValueError) as context:
            extract_html_content(page)

        self.assertIn("has no body content", str(context.exception))

    def test_body_without_storage_raises_value_error(self):
        """Test that body without storage raises ValueError."""
        page = {"body": {"view": {"value": "Some content"}}}

        with self.assertRaises(ValueError) as context:
            extract_html_content(page)

        self.assertIn("has no storage content", str(context.exception))

    def test_storage_without_value_raises_value_error(self):
        """Test that storage without value raises ValueError."""
        page = {"body": {"storage": {"representation": "storage"}}}

        with self.assertRaises(ValueError) as context:
            extract_html_content(page)

        self.assertIn("has no HTML value", str(context.exception))

    def test_extraction_with_confluence_macros(self):
        """Test extraction preserves Confluence macros in HTML."""
        html_with_macros = '<ac:structured-macro ac:name="info"><ac:rich-text-body><p>Info content</p></ac:rich-text-body></ac:structured-macro>'
        page = {"body": {"storage": {"value": html_with_macros}}}

        result = extract_html_content(page)

        self.assertEqual(result, html_with_macros)

    def test_extraction_with_empty_html(self):
        """Test extraction with empty HTML content."""
        page = {"body": {"storage": {"value": ""}}}

        result = extract_html_content(page)

        self.assertEqual(result, "")


class TestGetConfluencePageByIdHtml(unittest.TestCase):
    """Test cases for the get_confluence_page_by_id_html function.

    Tests successful HTML page retrieval by ID, error conditions, and content extraction.
    """

    def setUp(self):
        """Set up test fixtures and common test data."""
        self.page_id = "123456"
        self.mock_confluence = Mock()

    @patch("ai_tools_confluence.page.extract_html_content")
    def test_successful_page_retrieval_by_id_html(self, mock_extract):
        """Test successful retrieval and HTML extraction of page by ID."""
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_id.return_value = mock_page
        mock_extract.return_value = "<h1>Test</h1>"

        result = get_confluence_page_by_id_html(id=self.page_id, confluence=self.mock_confluence)

        self.mock_confluence.get_page_by_id.assert_called_once_with(self.page_id, expand="body.storage")
        mock_extract.assert_called_once_with(mock_page)
        self.assertEqual(result, "<h1>Test</h1>")

    @patch("ai_tools_confluence.page.extract_html_content")
    def test_page_with_confluence_macros(self, mock_extract):
        """Test retrieval of page with Confluence macros in HTML."""
        html_content = '<ac:structured-macro ac:name="toc"/>'
        mock_page = {"body": {"storage": {"value": html_content}}}
        self.mock_confluence.get_page_by_id.return_value = mock_page
        mock_extract.return_value = html_content

        result = get_confluence_page_by_id_html(id=self.page_id, confluence=self.mock_confluence)

        self.assertEqual(result, html_content)

    @patch("ai_tools_confluence.page.extract_html_content")
    def test_extraction_error_raises_value_error(self, mock_extract):
        """Test that extraction errors are caught and wrapped in ValueError."""
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_id.return_value = mock_page
        mock_extract.side_effect = ValueError("Missing body content")

        with self.assertRaises(ValueError) as context:
            get_confluence_page_by_id_html(id=self.page_id, confluence=self.mock_confluence)

        self.assertIn("Error extracting HTML from page with ID", str(context.exception))
        self.assertIn(self.page_id, str(context.exception))

    @patch("ai_tools_confluence.page.extract_html_content")
    def test_generic_exception_during_extraction(self, mock_extract):
        """Test handling of unexpected exceptions during HTML extraction."""
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_id.return_value = mock_page
        mock_extract.side_effect = Exception("Unexpected error")

        with self.assertRaises(ValueError) as context:
            get_confluence_page_by_id_html(id=self.page_id, confluence=self.mock_confluence)

        self.assertIn("Error extracting HTML from page with ID", str(context.exception))
        self.assertIn("Unexpected error", str(context.exception))


class TestGetConfluencePageByTitleHtml(unittest.TestCase):
    """Test cases for the get_confluence_page_by_title_html function.

    Tests successful HTML page retrieval by title and space, error conditions, and content extraction.
    """

    def setUp(self):
        """Set up test fixtures and common test data."""
        self.title = "My Test Page"
        self.space_key = "TESTSPACE"
        self.mock_confluence = Mock()

    @patch("ai_tools_confluence.page.extract_html_content")
    def test_successful_page_retrieval_by_title_html(self, mock_extract):
        """Test successful retrieval and HTML extraction of page by title."""
        mock_page = {"body": {"storage": {"value": "<p>Content</p>"}}}
        self.mock_confluence.get_page_by_title.return_value = mock_page
        mock_extract.return_value = "<p>Content</p>"

        result = get_confluence_page_by_title_html(
            title=self.title, space_key=self.space_key, confluence=self.mock_confluence
        )

        self.mock_confluence.get_page_by_title.assert_called_once_with(
            self.space_key, self.title, expand="body.storage"
        )
        mock_extract.assert_called_once_with(mock_page)
        self.assertEqual(result, "<p>Content</p>")

    @patch("ai_tools_confluence.page.extract_html_content")
    def test_page_with_special_characters_in_title_html(self, mock_extract):
        """Test retrieval of HTML page with special characters in title."""
        special_title = "Page: Testing & Development [2024]"
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_title.return_value = mock_page
        mock_extract.return_value = "<h1>Test</h1>"

        result = get_confluence_page_by_title_html(
            title=special_title, space_key=self.space_key, confluence=self.mock_confluence
        )

        self.mock_confluence.get_page_by_title.assert_called_once_with(
            self.space_key, special_title, expand="body.storage"
        )
        self.assertEqual(result, "<h1>Test</h1>")

    @patch("ai_tools_confluence.page.extract_html_content")
    def test_extraction_error_raises_value_error_with_title(self, mock_extract):
        """Test that extraction errors include the page title in error message."""
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_title.return_value = mock_page
        mock_extract.side_effect = ValueError("Missing storage content")

        with self.assertRaises(ValueError) as context:
            get_confluence_page_by_title_html(
                title=self.title, space_key=self.space_key, confluence=self.mock_confluence
            )

        self.assertIn("Error extracting HTML from page with title", str(context.exception))
        self.assertIn(self.title, str(context.exception))

    @patch("ai_tools_confluence.page.extract_html_content")
    def test_generic_exception_during_extraction_by_title(self, mock_extract):
        """Test handling of unexpected exceptions during HTML extraction by title."""
        mock_page = {"body": {"storage": {"value": "<h1>Test</h1>"}}}
        self.mock_confluence.get_page_by_title.return_value = mock_page
        mock_extract.side_effect = RuntimeError("Extraction failed")

        with self.assertRaises(ValueError) as context:
            get_confluence_page_by_title_html(
                title=self.title, space_key=self.space_key, confluence=self.mock_confluence
            )

        self.assertIn("Error extracting HTML from page with title", str(context.exception))
        self.assertIn("Extraction failed", str(context.exception))


if __name__ == "__main__":
    unittest.main()
