from typing import Any

from pydantic import BaseModel, Field

from .instance import Confluence


class ConfluenceCQLSearchInput(BaseModel):
    """Input schema for searching Confluence content."""

    cql_query: str = Field(
        description="CQL query string for searching content",
        examples=['text ~ "IPNEXT lifecycle" AND type=page', "type=blogpost AND space=BMWOSS"],
    )
    limit: int = Field(default=25, description="Maximum number of results to return")


class ConfluenceFreeTextSearchInput(BaseModel):
    """Input schema for performing a free-text Confluence page search."""

    text: str = Field(
        description="Free-text query string for page search",
        examples=["release notes", "CI/CD documentation"],
    )
    space_keys: list[str] | None = Field(
        default=None,
        description="Optional list of Confluence space keys to filter results",
    )
    limit: int = Field(default=25, description="Maximum number of page results to return")


def search_confluence_with_cql(
    cql_query: str,
    confluence: Confluence,
    limit: int = 25,
) -> str:
    """Search Confluence content using CQL (Confluence Query Language).

    Performs a search using CQL syntax to find pages, blog posts, and other
    content types in Confluence.

    Args:
        cql_query: CQL query string for searching content (e.g.,
            'text ~ "keyword" AND type=page').
        confluence: Confluence instance for API access.
        limit: Maximum number of results to return. Defaults to 25.

    Returns:
        Formatted string with search results showing page IDs and titles.

    Raises:
        Exception: If the CQL query is invalid or the API call fails.
    """
    res: dict[str, Any] = confluence.cql(  # pyright: ignore
        cql=cql_query,
        limit=limit,
    )

    search_result_texts = [f'Search Results for "{cql_query}" (- ID: TITLE):']

    for page in res.get("results", []):  # pyright: ignore
        search_result_texts.append("- {}: {}".format(page["content"]["id"], page["content"]["title"]))  # pyright: ignore

    return "\n".join(search_result_texts)


def _format_space_keys_for_cql(space_keys: list[str]) -> str:
    """Format space keys for inclusion in a CQL "space in" clause."""

    formatted_keys: list[str] = []
    for space_key in space_keys:
        stripped_key = space_key.strip()
        if not stripped_key:
            continue
        escaped_key = stripped_key.replace('"', '\\"')
        formatted_keys.append(f'"{escaped_key}"')
    return ", ".join(formatted_keys)


def search_confluence_pages_freetext(
    text: str,
    confluence: Confluence,
    limit: int = 25,
    space_keys: list[str] | None = None,
) -> str:
    """Search Confluence pages using a free-text query string.

    Performs a text search across page content, converting the input text
    to a CQL query. Optionally filters results by space keys.

    Args:
        text: Free-text query string used to find matching pages.
        confluence: Confluence instance for API access.
        limit: Maximum number of page results to return. Defaults to 25.
        space_keys: Optional list of space keys to constrain the search.

    Returns:
        Formatted string with search results showing page IDs and titles.

    Raises:
        Exception: If the search query is invalid or the API call fails.
    """

    escaped_text = text.replace('"', '\\"')
    cql_parts = [f'text ~ "{escaped_text}"', "type=page"]

    if space_keys:
        formatted_space_keys = _format_space_keys_for_cql(space_keys)
        if formatted_space_keys:
            cql_parts.append(f"space in ({formatted_space_keys})")

    cql_query = " AND ".join(cql_parts)

    res: dict[str, Any] = confluence.cql(  # pyright: ignore
        cql=cql_query,
        limit=limit,
    )

    search_result_texts = [f'Free text search results for "{text}" (- ID: TITLE):']

    for page in res.get("results", []):  # pyright: ignore
        search_result_texts.append("- {}: {}".format(page["content"]["id"], page["content"]["title"]))  # pyright: ignore

    return "\n".join(search_result_texts)
