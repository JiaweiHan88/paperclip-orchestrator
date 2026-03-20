"""Confluence page retrieval and content rendering utilities.

This module provides functions for fetching Confluence pages by ID or title,
and converting their content from Confluence's storage format to markdown
for better readability and AI processing.
"""

from typing import Any

from html_to_markdown import convert_to_markdown  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from .instance import Confluence


class GetConfluencePageByIdInput(BaseModel):
    """Input schema for retrieving a Confluence page by its unique ID.

    Used to specify which page to retrieve when the exact page ID is known.
    """

    id: str = Field(description="Confluence page ID")


def get_confluence_page_by_id(
    id: str,
    confluence: Confluence,
) -> str:
    """Retrieve and convert a Confluence page to markdown using its unique ID.

    This function fetches a Confluence page by its ID and converts the content
    from Confluence's storage format to markdown for better readability and
    processing by AI systems.

    Args:
        id: The unique identifier of the Confluence page to retrieve.
        confluence: An authenticated Confluence instance for API access.

    Returns:
        The page content rendered as markdown text, including titles, formatting,
        and structure converted from Confluence's storage format.

    Raises:
        ValueError: If the page cannot be found, accessed, or rendered. This can
                   occur if the page ID doesn't exist, the user lacks permissions,
                   or the page content is malformed.

    Example:
        >>> confluence = get_cc_confluence(token="my-token")
        >>> content = get_confluence_page_by_id("123456", confluence)
        >>> print(content)
        # Project Overview
        This is the project documentation...
    """
    # The atlassian library has untyped return values, so we need to handle this carefully
    page: dict[str, Any] = confluence.get_page_by_id(id, expand="body.storage")  # type: ignore[misc]

    try:
        return render_page_to_markdown(page)
    except Exception as e:
        raise ValueError(f"Error rendering page with ID '{id}': {e}") from e


class GetConfluencePageByTitleInput(BaseModel):
    """Input schema for retrieving a Confluence page by title within a space.

    Used when you know the page title and the space where it's located, which
    is often more user-friendly than using page IDs.
    """

    title: str = Field(description="Page title")
    space_key: str = Field(description="Space key where the page is located")


def get_confluence_page_by_title(
    title: str,
    space_key: str,
    confluence: Confluence,
) -> str:
    """Retrieve and convert a Confluence page to markdown using its title and space.

    This function finds a Confluence page by its title within a specific space
    and converts the content from Confluence's storage format to markdown for
    better readability and processing by AI systems.

    Args:
        title: The exact title of the Confluence page to retrieve.
        space_key: The key (short identifier) of the space containing the page.
        confluence: An authenticated Confluence instance for API access.

    Returns:
        The page content rendered as markdown text, including titles, formatting,
        and structure converted from Confluence's storage format.

    Raises:
        ValueError: If the page cannot be found, accessed, or rendered. This can
                   occur if the page title doesn't exist in the specified space,
                   the user lacks permissions, or the page content is malformed.

    Example:
        >>> confluence = get_atc_confluence(token="my-token")
        >>> content = get_confluence_page_by_title(
        ...     title="API Documentation",
        ...     space_key="DEV",
        ...     confluence=confluence
        ... )
        >>> print(content)
        # API Documentation
        ## Authentication
        All API calls require...
    """
    page: dict[str, Any] = confluence.get_page_by_title(space_key, title, expand="body.storage")  # type: ignore[misc]

    try:
        return render_page_to_markdown(page)
    except Exception as e:
        raise ValueError(f"Error rendering page with title '{title}': {e}") from e


def render_page_to_markdown(page: dict[str, Any] | None) -> str:
    """Convert a Confluence page from storage format to markdown.

    This function takes a Confluence page object (as returned by the Atlassian
    library) and converts its HTML storage content to markdown format using
    the html_to_markdown library.

    Args:
        page: The Confluence page data structure containing metadata and content.
              Expected to have a nested structure: body.storage.value containing
              the HTML content in Confluence storage format.

    Returns:
        The page content converted to markdown format, preserving structure
        like headings, lists, tables, and basic formatting.

    Raises:
        ValueError: If the page data is None, missing required fields, or has
                   malformed content structure. Specific error messages indicate
                   which part of the page structure is problematic.

    Note:
        This function expects the page to be fetched with "body.storage" expansion
        to ensure the content is available for conversion.
    """
    if page is None:
        raise ValueError("Page with not found")

    # Extract HTML content with proper error handling
    # Cast to dict for type checking, as we know the structure from the API
    page_dict = dict(page)  # type: ignore[arg-type]

    body: dict[str, Any] | None = page_dict.get("body")  # pyright: ignore
    if body is None:
        raise ValueError("Page with has no body content")

    storage: dict[str, Any] | None = dict(body).get("storage")  # type: ignore[arg-type]
    if storage is None:
        raise ValueError("Page with has no storage content")

    html_content: str | None = dict(storage).get("value")  # type: ignore[arg-type]
    if html_content is None:
        raise ValueError("Page with has no HTML value")

    return convert_to_markdown(html_content)


def extract_html_content(page: dict[str, Any] | None) -> str:
    """Extract raw HTML storage format from a Confluence page.

    This function takes a Confluence page object and returns its content
    in the original HTML storage format without markdown conversion.
    Useful for operations that need to preserve exact Confluence formatting,
    macros, and structure when updating pages.

    Args:
        page: The Confluence page data structure containing metadata and content.
              Expected to have a nested structure: body.storage.value containing
              the HTML content in Confluence storage format.

    Returns:
        The raw HTML content from Confluence's storage format, preserving all
        Confluence-specific markup, macros, and formatting.

    Raises:
        ValueError: If the page data is None, missing required fields, or has
                   malformed content structure. Specific error messages indicate
                   which part of the page structure is problematic.

    Note:
        This function expects the page to be fetched with "body.storage" expansion
        to ensure the content is available for extraction.
    """
    if page is None:
        raise ValueError("Page with not found")

    # Extract HTML content with proper error handling
    # Cast to dict for type checking, as we know the structure from the API
    page_dict = dict(page)  # type: ignore[arg-type]

    body: dict[str, Any] | None = page_dict.get("body")  # pyright: ignore
    if body is None:
        raise ValueError("Page with has no body content")

    storage: dict[str, Any] | None = dict(body).get("storage")  # type: ignore[arg-type]
    if storage is None:
        raise ValueError("Page with has no storage content")

    html_content: str | None = dict(storage).get("value")  # type: ignore[arg-type]
    if html_content is None:
        raise ValueError("Page with has no HTML value")

    return html_content


class GetConfluencePageByIdHtmlInput(BaseModel):
    """Input schema for retrieving a Confluence page's HTML content by its unique ID.

    Used when you need the raw HTML storage format instead of markdown,
    typically for page editing operations that preserve exact formatting.
    """

    id: str = Field(description="Confluence page ID")


def get_confluence_page_by_id_html(
    id: str,
    confluence: Confluence,
) -> str:
    """Retrieve a Confluence page's HTML storage format using its unique ID.

    This function fetches a Confluence page by its ID and returns the content
    in its original HTML storage format without markdown conversion. This is
    useful when you need to edit or update pages while preserving exact
    Confluence formatting, macros, and structure.

    Args:
        id: The unique identifier of the Confluence page to retrieve.
        confluence: An authenticated Confluence instance for API access.

    Returns:
        The page content in Confluence HTML storage format, preserving all
        Confluence-specific markup, macros, panels, and formatting.

    Raises:
        ValueError: If the page cannot be found, accessed, or rendered. This can
                   occur if the page ID doesn't exist, the user lacks permissions,
                   or the page content is malformed.

    Example:
        >>> confluence = get_cc_confluence(token="my-token")
        >>> html_content = get_confluence_page_by_id_html("123456", confluence)
        >>> print(html_content)
        <h1>Project Overview</h1>
        <p>This is the project documentation...</p>
        <ac:structured-macro ac:name="info">...</ac:structured-macro>
    """
    # The atlassian library has untyped return values, so we need to handle this carefully
    page: dict[str, Any] = confluence.get_page_by_id(id, expand="body.storage")  # type: ignore[misc]

    try:
        return extract_html_content(page)
    except Exception as e:
        raise ValueError(f"Error extracting HTML from page with ID '{id}': {e}") from e


class GetConfluencePageByTitleHtmlInput(BaseModel):
    """Input schema for retrieving a Confluence page's HTML content by title.

    Used when you need the raw HTML storage format and know the page title
    and space, typically for page editing operations that preserve exact formatting.
    """

    title: str = Field(description="Page title")
    space_key: str = Field(description="Space key where the page is located")


def get_confluence_page_by_title_html(
    title: str,
    space_key: str,
    confluence: Confluence,
) -> str:
    """Retrieve a Confluence page's HTML storage format using its title and space.

    This function finds a Confluence page by its title within a specific space
    and returns the content in its original HTML storage format without markdown
    conversion. This is useful when you need to edit or update pages while
    preserving exact Confluence formatting, macros, and structure.

    Args:
        title: The exact title of the Confluence page to retrieve.
        space_key: The key (short identifier) of the space containing the page.
        confluence: An authenticated Confluence instance for API access.

    Returns:
        The page content in Confluence HTML storage format, preserving all
        Confluence-specific markup, macros, panels, and formatting.

    Raises:
        ValueError: If the page cannot be found, accessed, or rendered. This can
                   occur if the page title doesn't exist in the specified space,
                   the user lacks permissions, or the page content is malformed.

    Example:
        >>> confluence = get_atc_confluence(token="my-token")
        >>> html_content = get_confluence_page_by_title_html(
        ...     title="API Documentation",
        ...     space_key="DEV",
        ...     confluence=confluence
        ... )
        >>> print(html_content)
        <h1>API Documentation</h1>
        <h2>Authentication</h2>
        <p>All API calls require...</p>
    """
    page: dict[str, Any] = confluence.get_page_by_title(space_key, title, expand="body.storage")  # type: ignore[misc]

    try:
        return extract_html_content(page)
    except Exception as e:
        raise ValueError(f"Error extracting HTML from page with title '{title}': {e}") from e
