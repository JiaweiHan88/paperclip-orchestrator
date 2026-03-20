"""Confluence comment functionality.

This module provides functions for adding comments to existing Confluence pages.
"""

from typing import Any

from pydantic import BaseModel, Field

from .instance import Confluence


class AddConfluenceCommentInput(BaseModel):
    """Input schema for adding a comment to a Confluence page.

    Used to specify which page to comment on and the comment text.
    """

    page_id: str = Field(description="The unique identifier of the page to add a comment to")
    comment: str = Field(
        description="The comment text in Confluence storage format (HTML). "
        "Can be plain text or HTML for formatted comments."
    )


def add_confluence_comment(
    page_id: str,
    comment: str,
    confluence: Confluence,
) -> str:
    """Add a comment to an existing Confluence page.

    This function adds a new comment to the specified Confluence page.
    Comments can include formatted text using Confluence's storage format (HTML).

    Args:
        page_id: The unique identifier of the Confluence page to comment on.
        comment: The comment text. Can be plain text or HTML formatted content
                using Confluence's storage format syntax.
        confluence: An authenticated Confluence instance for API access.

    Returns:
        Success message confirming the comment was added to the page.

    Raises:
        ValueError: If the comment cannot be added. This can occur if:
                   - The page ID doesn't exist
                   - The user lacks permissions to comment on the page
                   - The page is restricted or comments are disabled
                   - The operation fails due to server errors

    Example:
        >>> confluence = get_cc_confluence(token="my-token")
        >>> result = add_confluence_comment(
        ...     page_id="123456",
        ...     comment="<p>Great documentation! Just a note about...</p>",
        ...     confluence=confluence
        ... )
        >>> print(result)
        Successfully added comment to Confluence page '123456'
    """
    try:
        # Verify the page exists
        page_info: dict[str, Any] = confluence.get_page_by_id(  # type: ignore[assignment]
            page_id=page_id,
            expand="title",
        )

        if not page_info:
            raise ValueError(f"Page with ID '{page_id}' not found")

        page_title = page_info.get("title", "Unknown")

        # Add the comment to the page
        result: dict[str, Any] = confluence.add_comment(  # type: ignore[assignment]
            page_id=page_id,
            text=comment,
        )

        if not result:
            raise ValueError("Comment addition returned no result")

        comment_id = result.get("id", "unknown")  # type: ignore[union-attr]

        return f"Successfully added comment (ID: {comment_id}) to Confluence page '{page_title}' (ID: {page_id})"

    except Exception as e:
        raise ValueError(f"Failed to add comment to Confluence page '{page_id}': {str(e)}") from e
