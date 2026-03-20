"""Confluence page creation functionality.

This module provides functions for creating new Confluence pages in specified
spaces, with optional parent page relationships.
"""

from typing import Any

from pydantic import BaseModel, Field

from .instance import Confluence


class CreateConfluencePageInput(BaseModel):
    """Input schema for creating a new Confluence page.

    Used to specify the space, title, content, and optional parent page
    for the new page to be created.
    """

    space_key: str = Field(
        description="The key of the Confluence space where the page will be created (e.g., 'PROJ', 'TEAM')"
    )
    title: str = Field(description="The title of the new page")
    content: str = Field(
        description="Page content in Confluence storage format (HTML). "
        "Use Confluence's storage format syntax for proper rendering."
    )
    parent_id: str | None = Field(
        default=None,
        description="Optional ID of the parent page. If provided, the new page "
        "will be created as a child of this page.",
    )


def create_confluence_page(
    space_key: str,
    title: str,
    content: str,
    confluence: Confluence,
    parent_id: str | None = None,
) -> str:
    """Create a new Confluence page in the specified space.

    This function creates a new page with the provided title and content in
    the specified Confluence space. Optionally, the page can be created as
    a child of an existing parent page.

    Args:
        space_key: The key of the Confluence space (e.g., 'PROJ', 'TEAM').
        title: The title of the new page.
        content: Page content in Confluence storage format (HTML).
        confluence: An authenticated Confluence instance for API access.
        parent_id: Optional ID of the parent page. If provided, creates the page
                  as a child of the specified parent.

    Returns:
        Success message with the new page's ID, title, and URL.

    Raises:
        ValueError: If the page cannot be created. This can occur if:
                   - The space key doesn't exist
                   - The user lacks permissions to create pages in the space
                   - The parent page ID is invalid
                   - A page with the same title already exists in that location
                   - The creation operation fails due to server errors

    Example:
        >>> confluence = get_cc_confluence(token="my-token")
        >>> result = create_confluence_page(
        ...     space_key="PROJ",
        ...     title="New Project Documentation",
        ...     content="<p>This is the initial content</p>",
        ...     parent_id="123456",
        ...     confluence=confluence
        ... )
        >>> print(result)
        Successfully created Confluence page 'New Project Documentation' (ID: 789012)
    """
    try:
        # Create the page using the Confluence API
        result: dict[str, Any] = confluence.create_page(  # type: ignore[assignment]
            space=space_key,
            title=title,
            body=content,
            parent_id=parent_id if parent_id else None,
        )

        if not result:
            raise ValueError("Page creation returned no result")

        page_id = result.get("id", "unknown")
        page_title = result.get("title", title)

        # Build the page URL if available
        base_url = confluence.url.rstrip("/")
        page_url = f"{base_url}/pages/viewpage.action?pageId={page_id}"

        parent_info = f" as child of parent '{parent_id}'" if parent_id else ""

        return (
            f"Successfully created Confluence page '{page_title}' (ID: {page_id}) "
            f"in space '{space_key}'{parent_info}. "
            f"URL: {page_url}"
        )

    except Exception as e:
        raise ValueError(f"Failed to create Confluence page '{title}' in space '{space_key}': {str(e)}") from e
