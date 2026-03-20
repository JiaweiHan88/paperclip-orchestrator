"""Tool for searching code across GitHub repositories."""

import json
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field, model_validator

from ai_tools_github.github_client import Github

# Request text-match fragments from the REST API
_TEXT_MATCH_HEADERS = {"Accept": "application/vnd.github.text-match+json"}


class CodeSearchInput(BaseModel):
    """Input model for searching code on GitHub.

    At least ``query`` is required.  Optionally scope the search to a single
    repository (``owner`` **and** ``repo``) or to an entire organisation / user
    (``owner`` only).
    """

    query: str = Field(
        description=(
            "The search keywords or code snippet to look for. "
            "Supports GitHub search qualifiers such as 'language:python'."
        ),
        examples=["import torch", "TODO fix", "class MyHandler language:python"],
    )
    owner: str | None = Field(
        default=None,
        description=(
            "Repository owner (user or organisation) to narrow the search. "
            "When combined with ``repo`` the search is scoped to that single "
            "repository; when used alone it searches all repositories of the owner."
        ),
        examples=["software-factory", "octocat"],
    )
    repo: str | None = Field(
        default=None,
        description="Repository name.  Must be combined with ``owner``.",
        examples=["ai-tools-lib", "Hello-World"],
    )
    per_page: int = Field(
        default=30,
        description="Number of results to return (max 100).",
        ge=1,
        le=100,
    )

    @model_validator(mode="after")
    def _repo_requires_owner(self) -> "CodeSearchInput":
        if self.repo is not None and self.owner is None:
            raise ValueError("'repo' requires 'owner' to be set as well")
        return self


def _build_query(query: str, owner: str | None, repo: str | None) -> str:
    """Assemble the ``q`` parameter for the /search/code endpoint."""
    parts = [query]
    if owner and repo:
        parts.append(f"repo:{owner}/{repo}")
    elif owner:
        parts.append(f"org:{owner}")
    return " ".join(parts)


def _format_results(query: str, data: dict[str, Any]) -> str:
    """Turn the raw API JSON into a markdown string for the LLM."""
    total: int = data.get("total_count", 0)
    items: list[dict[str, Any]] = data.get("items", [])

    if not items:
        return f"No code results found for query: `{query}`"

    lines: list[str] = [
        "## Code Search Results",
        f"Found **{total}** result(s) for query: `{query}` (showing {len(items)}).\n",
    ]

    for item in items:
        repo_full = item.get("repository", {}).get("full_name", "unknown")
        path = item.get("path", "unknown")
        html_url = item.get("html_url", "")

        lines.append(f"### [{repo_full}: {path}]({html_url})")

        # Text-match fragments (only present with the text-match header)
        text_matches: list[dict[str, Any]] = item.get("text_matches", [])
        if text_matches:
            for tm in text_matches:
                fragment = tm.get("fragment", "")
                if fragment:
                    lines.append(f"```\n{fragment}\n```")
        lines.append("")  # blank separator

    return "\n".join(lines)


def search_code(
    query: str,
    github: Github,
    owner: str | None = None,
    repo: str | None = None,
    per_page: int = 30,
) -> str:
    """Search for code across GitHub repositories.

    Uses the GitHub REST API code search endpoint to find files matching the
    query.  Results include matched file paths, repository names and text
    fragments showing the match context.

    Args:
        query: Search keywords or code snippet to look for.
        github: GitHub instance for API access.
        owner: Optional owner (user / org) to narrow the search scope.
        repo: Optional repository name (requires ``owner``).
        per_page: Number of results per page (1-100, default 30).

    Returns:
        Markdown-formatted search results with file paths and match fragments.
    """
    full_query = _build_query(query, owner, repo)
    logger.info(f"Code search: q='{full_query}' per_page={per_page}")

    params = {"q": full_query, "per_page": str(per_page)}

    try:
        raw = github.v3_get(
            "/search/code",
            update_headers=_TEXT_MATCH_HEADERS,
            params=params,
        )
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to decode GitHub code search response as JSON")
        return "Error: received an invalid response from GitHub code search API."
    except Exception as exc:
        error_msg = str(exc)
        logger.error(f"Code search failed: {error_msg}")
        if "422" in error_msg:
            return (
                "Error: GitHub rejected the search query. "
                "This can happen when no scope qualifier (repo/org) is provided "
                "and the query is too broad. Try adding an owner or repo."
            )
        if "403" in error_msg:
            return "Error: rate limit exceeded or access denied."
        return f"Error: {error_msg}"

    return _format_results(full_query, data)
