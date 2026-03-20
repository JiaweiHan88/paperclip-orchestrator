"""Tool for fetching issues from a GitHub project board with filtering.

Filtering supports flexible key-value pairs. Use get_project_fields() to discover
available fields and their types. Common filter keys include:
- status: "open", "closed", "draft", or "all" (GitHub issue state)
- assignee: username string (use "@me" for current user, or "none" for unassigned)
- labels: list of label names (issues must have ALL specified labels)
- milestone: milestone title string (use "none" for no milestone)
- author: username string
- mentioned: username string

Project-specific custom fields (from get_project_fields) can also be filtered.
"""

from typing import Any, cast
from urllib.parse import urlsplit

from loguru import logger
from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github

# Type alias for flexible key-value filters
IssueFilters = dict[str, Any]


class ProjectBoardIssuesInput(BaseModel):
    """Input model for getting issues from a GitHub project board (no filters)."""

    project_url: str = Field(
        description="The URL of the GitHub project board.",
        examples=[
            "https://github.com/orgs/myorg/projects/1",
            "https://github.com/users/myuser/projects/2",
        ],
    )


class FilteredProjectBoardIssuesInput(BaseModel):
    """Input model for getting issues from a GitHub project board with filters."""

    project_url: str = Field(
        description="The URL of the GitHub project board.",
        examples=[
            "https://github.com/orgs/myorg/projects/1",
            "https://github.com/users/myuser/projects/2",
        ],
    )
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Key-value filters to apply. Use get_project_fields() to discover available fields. "
            "Common keys: status, assignee, labels, milestone, author, mentioned. "
            "Example: {'status': 'open', 'assignee': 'username', 'labels': ['bug', 'urgent']}"
        ),
    )


class ProjectFieldsInput(BaseModel):
    """Input model for getting project board fields."""

    project_url: str = Field(
        description="The URL of the GitHub project board.",
        examples=[
            "https://github.com/orgs/myorg/projects/1",
            "https://github.com/users/myuser/projects/2",
        ],
    )


def _parse_project_url(project_url: str) -> tuple[str, str, int]:
    """
    Parse a GitHub project URL to extract owner type, owner name, and project number.

    Args:
        project_url: The URL of the GitHub project board

    Returns:
        Tuple of (owner_type, owner_name, project_number) where owner_type is 'organization' or 'user'

    Raises:
        ValueError: If the URL format is invalid
    """
    split = urlsplit(project_url)
    path_parts = split.path.strip("/").split("/")

    if len(path_parts) < 4:
        raise ValueError(f"Invalid project URL format: {project_url}")

    if path_parts[0] == "orgs":
        owner_type = "organization"
        owner_name = path_parts[1]
    elif path_parts[0] == "users":
        owner_type = "user"
        owner_name = path_parts[1]
    else:
        raise ValueError(f"Unsupported project URL format: {project_url}")

    if path_parts[2] != "projects":
        raise ValueError(f"URL does not point to a projects board: {project_url}")

    try:
        project_number = int(path_parts[3])
    except ValueError:
        raise ValueError(f"Invalid project number in URL: {project_url}") from None

    return owner_type, owner_name, project_number


def get_project_fields(
    project_url: str,
    github: Github,
) -> dict[str, Any]:
    """
    Retrieve available fields for a GitHub project board.

    Args:
        project_url: The URL of the GitHub project board
        github: GitHub instance for API access

    Returns:
        Dict with:
        - project_id: The project's GraphQL ID
        - project_title: The project's title
        - standard_filters: Dict of standard filter keys with descriptions and options
        - fields: List of project-specific fields with name, field_type, and options
    """
    try:
        owner_type, owner_name, project_number = _parse_project_url(project_url)

        # Build the GraphQL query based on owner type
        if owner_type == "organization":
            owner_query = f'organization(login: "{owner_name}")'
        else:
            owner_query = f'user(login: "{owner_name}")'

        # Query to get project fields with their options
        query = f"""
        {owner_query} {{
            projectV2(number: {project_number}) {{
                id
                title
                fields(first: 50) {{
                    nodes {{
                        ... on ProjectV2Field {{
                            id
                            name
                            dataType
                        }}
                        ... on ProjectV2SingleSelectField {{
                            id
                            name
                            dataType
                            options {{
                                id
                                name
                            }}
                        }}
                        ... on ProjectV2IterationField {{
                            id
                            name
                            dataType
                            configuration {{
                                iterations {{
                                    id
                                    title
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """

        result = github.query(query)

        if not result:
            logger.error("No data returned from GraphQL query")
            return {"project_id": "", "project_title": "", "standard_filters": {}, "fields": []}

        if "errors" in result:
            logger.error(f"GraphQL errors: {result['errors']}")
            return {"project_id": "", "project_title": "", "standard_filters": {}, "fields": []}

        # Extract project data based on owner type
        owner_data = result.get("organization") or result.get("user")
        if not owner_data:
            logger.error("No owner data in response")
            return {"project_id": "", "project_title": "", "standard_filters": {}, "fields": []}

        project_data = owner_data.get("projectV2")
        if not project_data:
            logger.error("No project data in response")
            return {"project_id": "", "project_title": "", "standard_filters": {}, "fields": []}

        project_id = project_data.get("id", "")
        project_title = project_data.get("title", "")
        fields_data = project_data.get("fields", {}).get("nodes", [])

        # Transform field data
        fields: list[dict[str, Any]] = []
        for field in fields_data:
            if not field:
                continue

            field_name = field.get("name", "")
            field_type = field.get("dataType", "UNKNOWN")

            # Get options for single select fields
            options: list[str] = []
            if "options" in field:
                options = [opt.get("name", "") for opt in field.get("options", []) if opt]
            # Get iterations for iteration fields
            elif "configuration" in field:
                iterations = field.get("configuration", {}).get("iterations", [])
                options = [it.get("title", "") for it in iterations if it]

            field_dict: dict[str, Any] = {"name": field_name, "field_type": field_type}
            if options:
                field_dict["options"] = options
            fields.append(field_dict)

        # Define standard filters that are always available
        standard_filters: dict[str, dict[str, Any]] = {
            "status": {
                "description": "GitHub issue state",
                "type": "string",
                "options": ["open", "closed", "draft", "all"],
            },
            "assignee": {
                "description": "Filter by assignee username",
                "type": "string",
                "special_values": ["@me (current user)", "none (unassigned)"],
            },
            "labels": {
                "description": "Filter by label names (issues must have ALL specified labels)",
                "type": "list[string] or string",
                "special_values": ["none (no labels)"],
            },
            "milestone": {
                "description": "Filter by milestone title",
                "type": "string",
                "special_values": ["none (no milestone)"],
            },
            "author": {
                "description": "Filter by issue author username",
                "type": "string",
            },
            "mentioned": {
                "description": "Filter by user mentioned in the issue",
                "type": "string",
            },
        }

        return {
            "project_id": project_id,
            "project_title": project_title,
            "standard_filters": standard_filters,
            "fields": fields,
        }

    except Exception as e:
        raise Exception(f"Unable to fetch project fields: {str(e)}") from e


def _build_search_query(org: str, project_number: int, filters: IssueFilters) -> str:
    """
    Build a GitHub search query string from key-value filters.

    Args:
        org: The organization or user name
        project_number: The project board number
        filters: Dictionary of filter key-value pairs

    Returns:
        A GitHub search query string
    """
    query_parts: list[str] = [
        "is:issue",
        f"project:{org}/{project_number}",
    ]

    # Get filter values (case-insensitive key lookup)
    filter_lower = {k.lower(): v for k, v in filters.items()}

    # Add status filter
    status = filter_lower.get("status")
    if status:
        status_str = str(status).lower()
        if status_str == "open":
            query_parts.append("is:open")
        elif status_str == "closed":
            query_parts.append("is:closed")
        elif status_str == "draft":
            query_parts.append("draft:true")
        # "all" doesn't add any filter

    # Add assignee filter
    assignee = filter_lower.get("assignee")
    if assignee:
        if str(assignee).lower() == "none":
            query_parts.append("no:assignee")
        else:
            query_parts.append(f"assignee:{assignee}")

    # Add label filters
    labels = filter_lower.get("labels")
    if labels:
        if str(labels).lower() == "none":
            query_parts.append("no:label")
        elif isinstance(labels, list):
            for label in cast(list[str], labels):
                # Labels with spaces need to be quoted
                label_str = str(label)
                if " " in label_str:
                    query_parts.append(f'label:"{label_str}"')
                else:
                    query_parts.append(f"label:{label_str}")
        else:
            # Single label as string
            if " " in str(labels):
                query_parts.append(f'label:"{labels}"')
            else:
                query_parts.append(f"label:{labels}")

    # Add milestone filter
    milestone = filter_lower.get("milestone")
    if milestone:
        if str(milestone).lower() == "none":
            query_parts.append("no:milestone")
        elif " " in str(milestone):
            query_parts.append(f'milestone:"{milestone}"')
        else:
            query_parts.append(f"milestone:{milestone}")

    # Add author filter
    author = filter_lower.get("author")
    if author:
        query_parts.append(f"author:{author}")

    # Add mentioned filter
    mentioned = filter_lower.get("mentioned")
    if mentioned:
        query_parts.append(f"mentions:{mentioned}")

    return " ".join(query_parts)


def get_issues_from_project_board(
    project_url: str,
    github: Github,
    filters: IssueFilters | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch issues from a GitHub project board with optional filtering.

    This function retrieves issues from a specified GitHub project board
    using GraphQL. It extracts the project number and organization from the URL
    and queries GitHub's search API to find issues associated with the project.

    Use get_project_fields() to discover available filter fields and their types.

    Args:
        project_url: The URL of the GitHub project board
                    (e.g., "https://github.com/orgs/myorg/projects/1")
        github: GitHub instance for API access
        filters: Optional dict of key-value filters to apply.
                Common keys: status, assignee, labels, milestone, author, mentioned.
                Use get_project_fields() to see all available fields.

    Returns:
        List of issue dicts, each containing:
        - title: The issue title
        - body: The issue description
        - html_url: URL to the issue on GitHub
        - state: Issue state (open/closed)
        - assignees: List of assignee usernames
        - labels: List of label names

    Raises:
        ValueError: If the project URL format is invalid
        Exception: If the project board cannot be accessed or issues cannot be retrieved

    Examples:
        >>> github = get_cc_github_instance("token")
        >>> # Get all issues (no filter)
        >>> issues = get_issues_from_project_board(
        ...     "https://github.com/orgs/myorg/projects/1", github
        ... )
        >>> print(f"Found {len(issues)} issues")

        >>> # Get open issues
        >>> issues = get_issues_from_project_board(
        ...     "https://github.com/orgs/myorg/projects/1", github,
        ...     filters={"status": "open"}
        ... )

        >>> # Get issues by assignee and label
        >>> issues = get_issues_from_project_board(
        ...     "https://github.com/orgs/myorg/projects/1", github,
        ...     filters={"assignee": "username", "labels": ["bug", "high-priority"]}
        ... )
    """
    try:
        # Parse the project URL to extract organization and project number
        _, org, project_number = _parse_project_url(project_url)

        # Use empty dict if no filters provided
        if filters is None:
            filters = {}

        # Build the search query with filters
        search_query = _build_search_query(org, project_number, filters)

        # Use GitHub's search functionality to find issues in the project
        # Execute the GraphQL query directly with embedded search query
        result = github.query(
            f'search(type: ISSUE, first: 100, query: "{search_query}") {{'
            "issueCount "
            "pageInfo { endCursor hasNextPage } "
            "nodes { ...on Issue { "
            "title body url number state "
            "assignees(first: 10) { nodes { login } } "
            "labels(first: 20) { nodes { name } } "
            "} }"
            "}"
        )

        if not result:
            logger.error("No data returned from GraphQL query")
            return []

        if "errors" in result:
            logger.error(f"GraphQL errors: {result['errors']}")
            return []

        search_data = result["search"]
        issues_nodes = search_data.get("nodes", [])

        # Transform the data to a list of dicts
        issues: list[dict[str, Any]] = []
        for issue in issues_nodes:
            assignees_data = issue.get("assignees", {}).get("nodes", [])
            labels_data = issue.get("labels", {}).get("nodes", [])

            issues.append(
                {
                    "title": issue.get("title", ""),
                    "body": issue.get("body", ""),
                    "html_url": issue.get("url", ""),
                    "state": issue.get("state", "").lower(),
                    "assignees": [a.get("login", "") for a in assignees_data if a],
                    "labels": [lbl.get("name", "") for lbl in labels_data if lbl],
                }
            )

        return issues

    except Exception as e:
        raise Exception(f"Unable to fetch project board issues: {str(e)}") from e
