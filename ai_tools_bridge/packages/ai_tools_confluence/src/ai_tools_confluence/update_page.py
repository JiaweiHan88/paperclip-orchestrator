"""Confluence page update functionality.

This module provides functions for updating existing Confluence pages,
including modifying content, titles, and other page properties.
"""

from typing import Any

from pydantic import BaseModel, Field

from .instance import Confluence


class UpdateConfluencePageInput(BaseModel):
    """Input schema for updating an existing Confluence page.

    Used to specify which page to update and what changes to make.
    """

    page_id: str = Field(description="The unique identifier of the page to update")
    content: str = Field(
        description="New page content in Confluence storage format (HTML). "
        "Use Confluence's storage format syntax for proper rendering."
    )
    title: str | None = Field(
        default=None,
        description="Optional new title for the page. If not provided, keeps the existing title.",
    )


def update_confluence_page(
    page_id: str,
    content: str,
    confluence: Confluence,
    title: str | None = None,
) -> str:
    """Update an existing Confluence page with new content and/or title.

    This function fetches the current page version automatically and updates
    the page with the provided content. It handles version conflicts by always
    using the latest version from the server.

    Args:
        page_id: The unique identifier of the Confluence page to update.
        content: New page content in Confluence storage format (HTML).
                The content should use Confluence's storage format syntax.
        confluence: An authenticated Confluence instance for API access.
        title: Optional new title for the page. If None, the existing title is preserved.

    Returns:
        Success message with page details including page ID, title, and version.

    Raises:
        ValueError: If the page cannot be found or updated. This can occur if:
                   - The page ID doesn't exist
                   - The user lacks permissions to edit the page
                   - The page is restricted or locked
                   - The update operation fails due to server errors

    Example:
        >>> confluence = get_cc_confluence(token="my-token")
        >>> result = update_confluence_page(
        ...     page_id="123456",
        ...     content="<p>Updated content in HTML format</p>",
        ...     title="New Page Title",
        ...     confluence=confluence
        ... )
        >>> print(result)
        Successfully updated Confluence page '123456' to version 3
    """
    try:
        # Fetch the current page to get the title if not provided
        page_info: dict[str, Any] = confluence.get_page_by_id(  # type: ignore[assignment]
            page_id=page_id,
            expand="version",
        )

        if not page_info:
            raise ValueError(f"Page with ID '{page_id}' not found")

        current_title = page_info.get("title", "")

        # Use provided title or keep the existing one
        new_title = title if title is not None else current_title

        # Update the page (version is handled automatically by the API)
        result: dict[str, Any] = confluence.update_page(  # type: ignore[assignment]
            page_id=page_id,
            title=new_title,
            body=content,
        )

        new_version = result.get("version", {}).get("number", "unknown")  # type: ignore[union-attr]
        page_title = result.get("title", new_title)  # type: ignore[union-attr]

        return f"Successfully updated Confluence page '{page_title}' (ID: {page_id}) to version {new_version}"

    except Exception as e:
        raise ValueError(f"Failed to update Confluence page '{page_id}': {str(e)}") from e
