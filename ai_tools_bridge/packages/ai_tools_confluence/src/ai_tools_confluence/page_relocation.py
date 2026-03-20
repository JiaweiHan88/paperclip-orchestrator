"""Confluence page relocation utilities for moving and copying pages.

This module provides tools for relocating Confluence pages by moving them
to different parent pages or creating copies under new parents.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from .instance import Confluence


class RelocateConfluencePageInput(BaseModel):
    """Input schema for relocating a Confluence page (move or copy).

    Attributes:
        page_id: The unique identifier of the page to relocate.
        new_parent_id: The unique identifier of the new parent page.
        operation: The relocation operation - "move" (default) or "copy".
        new_title: Optional new title (only used for copy operation). If not
                  provided when copying, " (Copy)" will be appended to the
                  original title. Ignored for move operations.

    Examples:
        >>> # Move a page
        >>> input_data = RelocateConfluencePageInput(
        ...     page_id="123456",
        ...     new_parent_id="789012",
        ...     operation="move"
        ... )
        >>> # Copy a page with custom title
        >>> input_data = RelocateConfluencePageInput(
        ...     page_id="123456",
        ...     new_parent_id="789012",
        ...     operation="copy",
        ...     new_title="My Page Copy"
        ... )
    """

    page_id: str = Field(
        description="The unique identifier of the Confluence page to relocate",
        examples=["123456", "789012"],
    )
    new_parent_id: str = Field(
        description="The unique identifier of the new parent page",
        examples=["789012", "345678"],
    )
    operation: Literal["move", "copy"] = Field(
        default="move",
        description=(
            "The relocation operation: 'move' modifies the existing page's parent, "
            "'copy' creates a new page under the new parent"
        ),
        examples=["move", "copy"],
    )
    new_title: str | None = Field(
        default=None,
        description=(
            "Optional new title for the page. Only used when operation='copy'. "
            "If not provided, ' (Copy)' will be appended to the original title."
        ),
        examples=["My Page Copy", "Copied Documentation"],
    )


def relocate_confluence_page(
    page_id: str,
    new_parent_id: str,
    confluence: Confluence,
    operation: Literal["move", "copy"] = "move",
    new_title: str | None = None,
) -> str:
    """Relocate a Confluence page by moving or copying it to a different parent.

    This function can either move an existing page to a new parent (modifying
    the page's ancestor relationship) or create a copy of the page under a new
    parent. The operation is controlled by the 'operation' parameter.

    For move operations:
    - The page content and properties remain unchanged
    - Only the parent relationship is updated
    - Requires permissions on both source and target locations

    For copy operations:
    - Creates a new independent page with the same content
    - Child pages are not recursively copied
    - Original page remains unchanged

    Args:
        page_id: The unique identifier of the page to relocate.
        new_parent_id: The unique identifier of the new parent page.
        confluence: An authenticated Confluence instance for API access.
        operation: The relocation operation - "move" (default) or "copy".
        new_title: Optional new title. Only used for copy operations. If not
                  provided when copying, " (Copy)" will be appended to the
                  original title. Ignored for move operations.

    Returns:
        A success message confirming the operation with page details.

    Raises:
        ValueError: If the page cannot be found, accessed, or relocated. This can
                   occur if page IDs don't exist, user lacks permissions, or the
                   operation fails (e.g., duplicate title for copy).

    Examples:
        >>> confluence = get_cc_confluence(token="my-token")
        >>> # Move a page
        >>> result = relocate_confluence_page(
        ...     page_id="123456",
        ...     new_parent_id="789012",
        ...     confluence=confluence,
        ...     operation="move"
        ... )
        >>> print(result)
        Successfully moved page 'My Page' (ID: 123456) to parent 'Parent Page' (ID: 789012)

        >>> # Copy a page
        >>> result = relocate_confluence_page(
        ...     page_id="123456",
        ...     new_parent_id="789012",
        ...     confluence=confluence,
        ...     operation="copy",
        ...     new_title="My Page Copy"
        ... )
        >>> print(result)
        Successfully copied page 'My Page' to 'My Page Copy' (ID: 345678) under parent 'Parent Page' (ID: 789012)
    """
    try:
        # Fetch source page to get its content and metadata
        expand = "body.storage,space,version" if operation == "move" else "body.storage,space"
        source_page: dict[str, Any] = confluence.get_page_by_id(page_id, expand=expand)  # type: ignore[misc]
        source_title = source_page.get("title", "Unknown")
        body_content = source_page.get("body", {}).get("storage", {}).get("value", "")

        # Fetch parent page to validate it exists and get its title
        parent_page: dict[str, Any] = confluence.get_page_by_id(new_parent_id)  # type: ignore[misc]
        parent_title = parent_page.get("title", "Unknown")

        if operation == "move":
            # Update the existing page with new parent
            current_version = source_page.get("version", {}).get("number")
            if not current_version:
                raise ValueError(f"Could not determine version for page with ID '{page_id}'")

            confluence.update_page(  # type: ignore[misc]
                parent_id=new_parent_id,
                page_id=page_id,
                title=source_title,
                body=body_content,
                always_update=True,  # Force update even when content hasn't changed
            )

            return (
                f"Successfully moved page '{source_title}' (ID: {page_id}) "
                f"to parent '{parent_title}' (ID: {new_parent_id})"
            )

        else:  # operation == "copy"
            # Create a new page as a copy
            space_key = source_page.get("space", {}).get("key")
            if not space_key:
                raise ValueError(f"Could not determine space key for page with ID '{page_id}'")

            copy_title = new_title if new_title else f"{source_title} (Copy)"

            new_page: dict[str, Any] = confluence.create_page(  # type: ignore[misc]
                space=space_key,
                title=copy_title,
                body=body_content,
                parent_id=new_parent_id,
            )

            new_page_id = new_page.get("id", "Unknown")

            return (
                f"Successfully copied page '{source_title}' to '{copy_title}' "
                f"(ID: {new_page_id}) under parent '{parent_title}' (ID: {new_parent_id})"
            )

    except Exception as e:
        action = "moving" if operation == "move" else "copying"
        raise ValueError(f"Error {action} page with ID '{page_id}' to parent '{new_parent_id}': {e}") from e
