from typing import Any

from pydantic import BaseModel, Field

from .instance import Confluence


class GetConfluenceSpacesInput(BaseModel):
    """Input schema for getting Confluence spaces."""

    limit: int = Field(default=100, description="Maximum number of spaces to return")


class GetConfluencePageTreeInput(BaseModel):
    """Input schema for getting Confluence page tree."""

    space_key: str = Field(description="Space key to get pages from")
    root_page_id: str | None = Field(
        default=None,
        description="Optional root page ID to get children from. If not provided, gets all pages in space.",
    )
    limit: int = Field(default=100, description="Maximum number of pages to return")


def get_confluence_spaces(
    confluence: Confluence,
    limit: int = 100,
) -> str:
    """Get all Confluence spaces with key, title and description.

    Retrieves a list of accessible Confluence spaces including their
    metadata such as key, name, and description.

    Args:
        confluence: Confluence instance for API access.
        limit: Maximum number of spaces to return. Defaults to 100.

    Returns:
        Markdown formatted list of spaces with key, title and description.

    Raises:
        Exception: If the API call fails or access is denied.
    """
    spaces: dict[str, Any] = confluence.get_all_spaces(  # pyright: ignore
        start=0,
        limit=limit,
        expand="description,icon,homepage",
    )

    result_lines = ["# Confluence Spaces\n"]

    for space in spaces.get("results", []):  # pyright: ignore
        key: str = space.get("key", "N/A")  # pyright: ignore
        name: str = space.get("name", "N/A")  # pyright: ignore

        # Extract description text if available
        description_text = "No description"
        description_obj: dict[str, Any] | None = space.get("description")  # pyright: ignore
        if description_obj:
            plain_obj: dict[str, Any] | None = description_obj.get("plain")  # pyright: ignore
            if plain_obj:
                desc_value: str | None = plain_obj.get("value")  # pyright: ignore
                if desc_value and desc_value.strip():
                    description_text = desc_value.strip()

        result_lines.append(f"## {name}")
        result_lines.append(f"- **Key**: `{key}`")
        result_lines.append(f"- **Description**: {description_text}\n")

    return "\n".join(result_lines)


def get_confluence_page_tree(
    space_key: str,
    confluence: Confluence,
    root_page_id: str | None = None,
    limit: int = 100,
) -> str:
    """Get page tree for a space or under a specific page.

    Retrieves the hierarchical structure of pages in a Confluence space.
    If an error is returned with no access, try the space key in lower
    or upper case.

    Args:
        space_key: Space key to get pages from.
        confluence: Confluence instance for API access.
        root_page_id: Optional root page ID to get children from. If not
            provided, gets all pages in space.
        limit: Maximum number of pages to return. Defaults to 100.

    Returns:
        Indented markdown list with page IDs and titles showing tree structure.

    Raises:
        Exception: If the space key is invalid, access is denied, or the
            API call fails.
    """
    if root_page_id:
        # get_child_pages returns a list directly
        result: list[Any] = confluence.get_child_pages(page_id=root_page_id)  # pyright: ignore
        pages: list[dict[str, Any]] = [dict(p) for p in result] if result else []  # type: ignore[arg-type]
    else:
        result_dict: dict[str, Any] = confluence.get_all_pages_from_space(  # pyright: ignore
            space=space_key,
            start=0,
            limit=limit,
            expand="ancestors,space",
        )
        pages = [dict(p) for p in result_dict] if result_dict else []  # type: ignore[arg-type]

    # Build a map of page_id -> page data
    page_map: dict[str, dict[str, Any]] = {}
    for page in pages:
        page_dict: dict[str, Any] = dict(page)  # type: ignore[arg-type]
        page_id: str = page_dict.get("id", "")
        page_map[page_id] = {
            "id": page_id,
            "title": page_dict.get("title", "Untitled"),
            "parent_id": page_dict.get("ancestors", [{}])[-1].get("id") if page_dict.get("ancestors") else None,
            "children": [],
        }

    # Build tree structure
    root_pages: list[str] = []
    for page_id, page_data in page_map.items():
        parent_id = page_data["parent_id"]
        if parent_id and parent_id in page_map:
            page_map[parent_id]["children"].append(page_id)
        else:
            root_pages.append(page_id)

    # Format as indented list
    result_lines = [f"# Page Tree for Space: {space_key}\n"]

    def format_tree(page_id: str, indent_level: int = 0) -> None:
        """Recursively format page tree with indentation."""
        page_data = page_map[page_id]
        indent = "  " * indent_level
        result_lines.append(f"{indent}- {page_data['id']}: {page_data['title']}")

        # Sort children for consistent output
        for child_id in sorted(page_data["children"]):
            format_tree(child_id, indent_level + 1)

    # Format all root pages
    for page_id in sorted(root_pages):
        format_tree(page_id)

    return "\n".join(result_lines)
