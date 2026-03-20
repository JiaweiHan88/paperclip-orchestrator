import re
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlsplit

from jinja2 import Environment, FileSystemLoader
from loguru import logger
from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github
from ai_tools_github.models.issue import (
    CrossReferencedEvent,
    Issue,
)
from ai_tools_github.models.issue import (
    CrossReferencedSource as PullRequest,
)
from ai_tools_github.models.issue import (
    IssueComment as Comment,
)
from ai_tools_github.utils.filtering_functions import (
    is_author_login_bot,
    is_author_unwanted,
    is_content_unwanted,
    is_retrigger_comment,
    login_startswith_tu,
)

from .instance import get_cc_github_instance

URL_GRAPHQL_API = "https://cc-github.bmwgroup.net/api/graphql"

QUERY_ISSUE_DATA = """
title
number
url
body
bodyHTML
labels(last: 10) {
    nodes {
    name
    }
}
comments(last: 100) {
    nodes {
    body
    bodyHTML
    author {
        login
    }
    createdAt
    }
}
timelineItems(last: 50, itemTypes: [CROSS_REFERENCED_EVENT, REFERENCED_EVENT]) {
    nodes {
    __typename
    ... on CrossReferencedEvent {
        createdAt
        source {
        __typename
        ... on PullRequest {
            number
            title
            url
            merged
        }
        ... on Issue {
            title
            number
            url
            body
            labels(last: 10) {
                nodes {
                name
                }
            }
        }
        }
    }
    __typename
    ... on ReferencedEvent {
        createdAt
        commit {
        oid
        message
        committedDate
        }
    }
    }
}
"""


class StructuredIssueData(BaseModel):
    """Structured issue data"""

    grouped_links: dict[str, list[str]] | None = Field(default_factory=dict[str, list[str]])
    images: list[str] | None = Field(default_factory=list[str])
    issue: Issue | None = None
    linked_prs: list[PullRequest] | None = Field(default_factory=list[PullRequest])


class GitHubIssueExtractorInput(BaseModel):
    """Input model for getting information of a github issue."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["swh", "software-factory"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo1", "xpad-shared"],
    )
    number: int = Field(
        description="The number of the issue.",
        examples=[134, 83733],
    )


class GitHubIssueExtractor:
    """
    Tool for extracting information from GitHub issues and formatting that information
    into markdown.

    Uses GraphQL to access the data of that issue.
    Provide the owner name, the repo name and the issue number to communicate
    with the graphQL API. The information from the issue is fetched and then
    filtered using the functions from filter_comments.py. This ensures comments
    from unwanted authors (bots) or with unwanted content (retriggered comments) are
    not included for further analysis.

    The author_filters and content_filters in filter_comments.py are adjustable.

    After fetching and filtering, the information is returned as a markdown text.

    """

    def __init__(self, github_token: str, owner: str, repo: str, number: int) -> None:
        logger.info(f"Initializing the tool {self.__class__.__name__}.")

        self.github_token = github_token
        self.owner = owner
        self.repo = repo
        self.number = number

        # Initialize the Github instance
        self.github = get_cc_github_instance(self.github_token)

    def get_issue_data(self) -> str:
        """
        Run the tool. Fetch the data from a GitHub issue, structure the data and
        render it to markdown using jinja2.

        Args:
            owner (str): Owner of the repository.
            repo (str): Name of the repository.
            number (int): Issue number.

        Returns:
            markdown_output (str): The markdown data using a jinja2 template.

        """
        raw_issue_data = self.github.query(
            f'repository(owner:"{self.owner}", name:"{self.repo}")'
            f"{{ issue(number:{self.number}) {{ {QUERY_ISSUE_DATA} }} }}"
        )

        structured_issue_data = self._structure_and_filter_issue_data(raw_issue_data)
        markdown_output = self._to_markdown(structured_issue_data)
        markdown_output = self._sanitize_authors(markdown_output)
        return markdown_output

    def _structure_and_filter_issue_data(self, raw_issue_data: dict[str, Any]) -> StructuredIssueData:
        """
        Structure and filter the raw response data, then use an instance
        of StructuredIssueData to store the data.

        Extract the issue data. Filter out unwanted comments (e.g. from bots).
        Extract references, cross references, linked PRs, image URLs and
        extract and group all links.

        Args:
            raw_issue_data (str): The raw data from the response.

        Returns:
            structured_issue_data (StructuredIssueData): The structured data of
                the issue.

        """
        issue_data = raw_issue_data["repository"]["issue"]
        issue = Issue(**issue_data)
        issue = self._apply_comment_filters(issue)

        # Get all linked PRs from the timeline items
        assert issue.timeline_items is not None, "Issue timeline_items must not be None"
        linked_prs: list[PullRequest] = []
        for item in issue.timeline_items:
            if not isinstance(item, CrossReferencedEvent):
                continue

            assert item.source is not None, "CrossReferencedEvent source must not be None"
            if item.source.typename == "PullRequest":
                linked_prs.append(item.source)

        # Extract and group all URLs
        grouped_links = self._extract_and_group_urls(issue)

        # Get all linked PRs from the text of the issue
        linked_prs = self._add_linked_prs(grouped_links, linked_prs)

        # Extract all image URLs from the HTML
        image_urls = self._extract_image_urls(issue)

        logger.info("Finished structuring issue data.")
        return StructuredIssueData(
            issue=issue,
            images=image_urls,
            linked_prs=linked_prs,
            grouped_links=grouped_links,
        )

    def _apply_comment_filters(self, issue: Issue) -> Issue:
        """
        Apply comment filtering.

        Filter out unwanted comments (e.g. from bots).
        Filter out comments from unwanted authors or with unwanted content.

        Args:
            issue (Issue): The issue object.

        Returns:
            issue (Issue): The issue object with filtered comments.

        """
        logger.info("Filtering out unwanted comments (from Bots e.g.).")
        assert issue.comments is not None, "Issue comments must not be None"
        len_all_comments = len(issue.comments)
        filtered_comments: list[Comment] = []

        for comment in issue.comments:
            assert comment.author is not None, "Comment author must not be None"
            assert comment.author.login is not None, "Comment author login must not be None"
            assert comment.body is not None, "Comment body must not be None"

            if not (
                login_startswith_tu(comment.author.login)
                or is_author_login_bot(comment.author.login)
                or is_author_unwanted(comment.author.login)
                or is_retrigger_comment(comment.body)
                or is_content_unwanted(comment.body)
            ):
                filtered_comments.append(comment)

        logger.info(
            f"Removed {len_all_comments - len(filtered_comments)} comment(s). "
            f"From {len_all_comments} "
            f"to {len(filtered_comments)}."
        )

        issue.comments = filtered_comments
        return issue

    def _extract_and_group_urls(self, issue: Issue) -> dict[str, list[str]]:
        """
        Extract and group URLs.

        Args:
            issue (Issue): The issue object.

        Returns:
            grouped_urls (dict[str, list[str]]): A dictionary with grouped urls:
            {
                "https://cc-github.company-name.net": [...],
                "https://cc-ci.company-name.net": [...]
            }

        """
        logger.info("Extracting and grouping URLs.")
        assert issue.comments is not None, "Issue comments must not be None"
        assert issue.body is not None, "Issue body must not be None"
        assert issue.title is not None, "Issue title must not be None"

        comment_bodies: list[str] = []
        for comment in issue.comments:
            assert comment.body is not None, "Comment body must not be None"
            comment_bodies.append(comment.body)

        combined_text = " ".join(
            [
                issue.title,
                issue.body,
                *comment_bodies,
            ]
        )

        # Find URLs using regex
        url_pattern = r"https?://[^\s)]+"
        urls: list[str] = re.findall(url_pattern, combined_text)

        # Group URLs by domain
        grouped_urls: defaultdict[str, list[str]] = defaultdict(list)
        for url in urls:
            # Trim whitespace and remove trailing punctuation like commas, etc.
            url = url.strip().rstrip(",.;:")
            domain = urlparse(url).netloc
            grouped_urls[domain].append(url)

        # Deduplicate and sort each list of URLs
        deduplicated_grouped_urls = {domain: sorted(set(url_list)) for domain, url_list in grouped_urls.items()}
        return dict(deduplicated_grouped_urls)

    def _add_linked_prs(self, grouped_links: dict[str, list[str]], linked_prs: list[PullRequest]) -> list[PullRequest]:
        """
        Extract PR URLs from grouped_links and return PullRequest objects for those
        not already in linked_prs.

        Args:
            grouped_links (dict[str, list[str]]): Dictionary of all
                found links, grouped by domain.
            linked_prs (list[PullRequest]): List of all linked PRs in
                the timeline events.

        Returns:
            list[PullRequest]: Combined list of existing and newly found linked PRs.

        """
        logger.info("Extracting linked PR URLs from all present URLs.")

        # Flatten all links from all groups
        all_links = [link for group in grouped_links.values() for link in group]

        # Extract PR URLs using regex
        pr_url_pattern = r"https?://[^ ]*github[^ ]*/[^ ]+/[^ ]+/pull/\d+"
        found_pr_urls = set(re.findall(pr_url_pattern, " ".join(all_links)))

        # Get URLs of already linked PRs
        existing_pr_urls: set[str] = set()
        for pr in linked_prs:
            assert pr.url is not None, "PullRequest URL must not be None"
            existing_pr_urls.add(pr.url)

        # Filter out already known PRs
        new_pr_urls = found_pr_urls - existing_pr_urls

        # Create new PullRequest objects
        new_prs = [PullRequest(url=url) for url in new_pr_urls]

        return linked_prs + new_prs

    def _get_image_urls(self, html_content: str) -> list[str]:
        """
        Extract image URLs from HTML content using a regular expression.

        Args:
            html_content (str): The HTML-encoded string to search for image tags.

        Returns:
            list[str]: A list of image URLs extracted from <img src="..."> tags.

        """
        return re.findall(r'<img[^>]+src="([^">]+)"', html_content or "")

    def _extract_image_urls(self, issue: Issue) -> list[str]:
        """
        Extract image URLs from the HTML body and comments of a GitHub issue.

        Args:
            issue (Issue): The issue object containing HTML-rendered
                body and comments.

        Returns:
            list[str]: A list of unique image URLs found in the issue's
                body and its comments.

        """
        logger.info("Extracting image URLs from the issue's body and its comments.")

        # Extract image URLs from issue bodyHTML
        assert issue.body_html is not None, "Issue body_html must not be None"
        issue_images = self._get_image_urls(issue.body_html)

        # Extract image URLs from each comment's bodyHTML
        assert issue.comments is not None, "Issue comments must not be None"
        comment_images: list[str] = []
        for comment in issue.comments:
            assert comment.body_html is not None, "Comment body_html must not be None"
            comment_images.extend(self._get_image_urls(comment.body_html))

        # Combine and deduplicate
        image_urls = list(set(issue_images + comment_images))
        image_urls = sorted(image_urls)
        return image_urls

    def _sanitize_authors(self, md_output: str) -> str:
        """
        Replace all user mentions in the text with 'Author'.
        Also replaces lines with 'Reviewed-by:' with an empty line.

        Args:
            md_output (md_output): The markdown output.

        Returns:
            md_output (md_output): The sanitized markdown output.

        """
        logger.info("Sanitizing author mentions in the markdown.")
        md_output = re.sub(
            r"^Reviewed-by:.*\r?\n?",
            "",
            md_output,
            flags=re.MULTILINE,
        ).strip()
        md_output = re.sub(r"@\w+", "@Author", md_output)
        return md_output

    def _to_markdown(self, structured_issue_data: StructuredIssueData) -> str:
        """
        Render the structured_issue_data into markdown using a jinja2 markdown template.

        Args:
            structured_issue_data (StructuredIssueData): The issue data
                in a structured format.

        Returns:
            md_output (str): The markdown output string.

        """
        logger.info("Rendering data to markdown.")
        template_dir = Path(__file__).resolve().parent / "templates"
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("template_issues.md.j2")
        md_output = template.render(structured_issue_data=structured_issue_data)
        return md_output


class CreateIssueInput(BaseModel):
    """Input model for creating a new GitHub issue."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["swh", "software-factory"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo1", "xpad-shared"],
    )
    title: str = Field(
        description="The title of the issue.",
        examples=["Bug: Login page not loading", "Feature request: Dark mode support"],
    )
    body: str | None = Field(
        default=None,
        description="The body/description of the issue (optional). Supports markdown formatting.",
        examples=[
            "## Problem\nThe login page fails to load when...\n\n## Steps to reproduce\n1. Go to login page\n2. ...",
            None,
        ],
    )
    labels: list[str] | None = Field(
        default=None,
        description="List of label names to add to the issue (optional).",
        examples=[["bug", "high-priority"], ["enhancement", "documentation"]],
    )
    assignees: list[str] | None = Field(
        default=None,
        description="List of GitHub usernames to assign to the issue (optional).",
        examples=[["username1", "username2"]],
    )
    milestone: str | None = Field(
        default=None,
        description="Milestone title to associate with the issue (optional).",
        examples=["v1.0.0", "Sprint 3"],
    )
    project_url: str | None = Field(
        default=None,
        description=(
            "URL of a GitHub project board to link the issue to (optional). "
            "The issue will be added to this project board after creation."
        ),
        examples=[
            "https://github.com/orgs/myorg/projects/1",
            "https://github.com/users/myuser/projects/2",
        ],
    )
    custom_fields: dict[str, str] | None = Field(
        default=None,
        description=(
            "Dictionary of custom field names to values for the project board (optional). "
            "Use get_project_fields() to discover available fields and their types/options. "
            "For single-select fields, use the option name. For text fields, provide the text value. "
            "For number fields, provide a numeric string. For date fields, use ISO format (YYYY-MM-DD)."
        ),
        examples=[
            {"Status": "In Progress", "Priority": "High"},
            {"Sprint": "Sprint 1", "Effort": "3"},
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


def _get_project_id(project_url: str, github: Github) -> str | None:
    """
    Get the project ID from a project URL.

    Args:
        project_url: The URL of the GitHub project board
        github: GitHub instance for API access

    Returns:
        The project's GraphQL ID or None if not found
    """
    try:
        owner_type, owner_name, project_number = _parse_project_url(project_url)

        # Build the GraphQL query based on owner type
        if owner_type == "organization":
            owner_query = f'organization(login: "{owner_name}")'
        else:
            owner_query = f'user(login: "{owner_name}")'

        query = f"""
        {owner_query} {{
            projectV2(number: {project_number}) {{
                id
            }}
        }}
        """

        result = github.query(query)

        if not result or "errors" in result:
            logger.error(f"Failed to get project ID: {result}")
            return None

        owner_data = result.get("organization") or result.get("user")
        if not owner_data:
            return None

        project_data = owner_data.get("projectV2")
        if not project_data:
            return None

        return project_data.get("id")

    except Exception as e:
        logger.error(f"Error getting project ID: {e}")
        return None


def _add_issue_to_project(issue_id: str, project_id: str, github: Github) -> str | None:
    """
    Add an issue to a project board.

    Args:
        issue_id: The GraphQL ID of the issue
        project_id: The GraphQL ID of the project
        github: GitHub instance for API access

    Returns:
        The project item ID if successful, None otherwise
    """
    try:
        mutation = f"""
        mutation {{
            addProjectV2ItemById(input: {{
                projectId: "{project_id}"
                contentId: "{issue_id}"
            }}) {{
                item {{
                    id
                }}
            }}
        }}
        """

        result = github.query(mutation)

        if "errors" in result:
            logger.error(f"Failed to add issue to project: {result['errors']}")
            return None

        item = result.get("addProjectV2ItemById", {}).get("item")
        return item.get("id") if item else None

    except Exception as e:
        logger.error(f"Error adding issue to project: {e}")
        return None


def _get_project_fields_info(project_url: str, github: Github) -> dict[str, dict[str, Any]]:
    """
    Get detailed field information for a project, including field IDs and option IDs.

    Args:
        project_url: The URL of the GitHub project board
        github: GitHub instance for API access

    Returns:
        Dictionary mapping field names to their details (id, dataType, options with IDs)
    """
    try:
        owner_type, owner_name, project_number = _parse_project_url(project_url)

        if owner_type == "organization":
            owner_query = f'organization(login: "{owner_name}")'
        else:
            owner_query = f'user(login: "{owner_name}")'

        query = f"""
        {owner_query} {{
            projectV2(number: {project_number}) {{
                id
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

        if not result or "errors" in result:
            logger.error(f"Failed to get project fields: {result}")
            return {}

        owner_data = result.get("organization") or result.get("user")
        if not owner_data:
            return {}

        project_data = owner_data.get("projectV2")
        if not project_data:
            return {}

        fields_data = project_data.get("fields", {}).get("nodes", [])
        fields_map: dict[str, dict[str, Any]] = {}

        for field in fields_data:
            if not field or not field.get("name"):
                continue

            field_name = field.get("name")
            field_info: dict[str, Any] = {
                "id": field.get("id"),
                "dataType": field.get("dataType"),
            }

            # For single select fields, include options with their IDs
            if "options" in field:
                field_info["options"] = {opt.get("name"): opt.get("id") for opt in field.get("options", []) if opt}

            # For iteration fields, include iterations with their IDs
            elif "configuration" in field:
                iterations = field.get("configuration", {}).get("iterations", [])
                field_info["options"] = {it.get("title"): it.get("id") for it in iterations if it}

            fields_map[field_name] = field_info

        return fields_map

    except Exception as e:
        logger.error(f"Error getting project fields info: {e}")
        return {}


def _set_project_field_value(
    project_id: str,
    item_id: str,
    field_id: str,
    field_type: str,
    value: str,
    option_id: str | None,
    github: Github,
) -> bool:
    """
    Set a field value for a project item.

    Args:
        project_id: The GraphQL ID of the project
        item_id: The GraphQL ID of the project item
        field_id: The GraphQL ID of the field
        field_type: The data type of the field (TEXT, NUMBER, DATE, SINGLE_SELECT, ITERATION)
        value: The value to set
        option_id: The option ID for single-select or iteration fields
        github: GitHub instance for API access

    Returns:
        True if the field was successfully set, False otherwise
    """
    try:
        # Build the value part based on field type
        if field_type == "SINGLE_SELECT":
            if not option_id:
                logger.error(f"Option ID required for single-select field, value: {value}")
                return False
            value_part = f'singleSelectOptionId: "{option_id}"'
        elif field_type == "ITERATION":
            if not option_id:
                logger.error(f"Iteration ID required for iteration field, value: {value}")
                return False
            value_part = f'iterationId: "{option_id}"'
        elif field_type == "NUMBER":
            try:
                num_value = float(value)
                value_part = f"number: {num_value}"
            except ValueError:
                logger.error(f"Invalid number value: {value}")
                return False
        elif field_type == "DATE":
            value_part = f'date: "{value}"'
        else:  # TEXT and other types
            escaped_value = value.replace('"', '\\"')
            value_part = f'text: "{escaped_value}"'

        mutation = f"""
        mutation {{
            updateProjectV2ItemFieldValue(input: {{
                projectId: "{project_id}"
                itemId: "{item_id}"
                fieldId: "{field_id}"
                value: {{{value_part}}}
            }}) {{
                projectV2Item {{
                    id
                }}
            }}
        }}
        """

        result = github.query(mutation)

        if "errors" in result:
            logger.error(f"Failed to set field value: {result['errors']}")
            return False

        return result.get("updateProjectV2ItemFieldValue", {}).get("projectV2Item") is not None

    except Exception as e:
        logger.error(f"Error setting field value: {e}")
        return False


def _set_custom_fields_on_item(
    project_url: str,
    project_id: str,
    item_id: str,
    custom_fields: dict[str, str],
    github: Github,
) -> dict[str, bool]:
    """
    Set multiple custom field values on a project item.

    Args:
        project_url: The URL of the GitHub project board
        project_id: The GraphQL ID of the project
        item_id: The GraphQL ID of the project item
        custom_fields: Dictionary of field names to values
        github: GitHub instance for API access

    Returns:
        Dictionary mapping field names to success status (True/False)
    """
    results: dict[str, bool] = {}

    # Get field information
    fields_info = _get_project_fields_info(project_url, github)
    if not fields_info:
        logger.error("Could not retrieve project fields information")
        return dict.fromkeys(custom_fields, False)

    for field_name, value in custom_fields.items():
        if field_name not in fields_info:
            logger.warning(f"Field '{field_name}' not found in project. Available fields: {list(fields_info.keys())}")
            results[field_name] = False
            continue

        field_info = fields_info[field_name]
        field_id = field_info.get("id")
        field_type = field_info.get("dataType", "TEXT")

        if not field_id:
            logger.error(f"No field ID found for field: {field_name}")
            results[field_name] = False
            continue

        # Get option ID for single-select or iteration fields
        option_id = None
        if field_type in ("SINGLE_SELECT", "ITERATION"):
            options = field_info.get("options", {})
            option_id = options.get(value)
            if not option_id:
                logger.warning(
                    f"Value '{value}' not found in options for field '{field_name}'. "
                    f"Available options: {list(options.keys())}"
                )
                results[field_name] = False
                continue

        success = _set_project_field_value(
            project_id=project_id,
            item_id=item_id,
            field_id=field_id,
            field_type=field_type,
            value=value,
            option_id=option_id,
            github=github,
        )
        results[field_name] = success

    return results


def create_issue(
    owner: str,
    repo: str,
    title: str,
    github: Github,
    body: str | None = None,
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
    milestone: str | None = None,
    project_url: str | None = None,
    custom_fields: dict[str, str] | None = None,
) -> str:
    """Create a new issue in a GitHub repository.

    Creates an issue with the specified title, body, and optional metadata.
    Can also link the issue to a project board and set custom fields.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        title: The title of the issue.
        github: GitHub instance for API access.
        body: The body/description of the issue (optional).
        labels: List of label names to add to the issue (optional).
        assignees: List of GitHub usernames to assign to the issue (optional).
        milestone: Milestone title to associate with the issue (optional).
        project_url: URL of a GitHub project board to link the issue to (optional).
        custom_fields: Dictionary of custom field names to values for the project board (optional).
            Use get_project_fields() to discover available fields and their types/options.
            For single-select fields, use the option name. For text fields, provide the text value.
            For number fields, provide a numeric string. For date fields, use ISO format (YYYY-MM-DD).

    Returns:
        Markdown formatted information about the created issue, including URL.

    Raises:
        Exception: If the repository ID cannot be retrieved or issue creation fails.
    """
    logger.info(f"Creating issue in {owner}/{repo}: {title}")

    try:
        # First, get the repository ID
        repo_query = f"""
        repository(owner: "{owner}", name: "{repo}") {{
            id
        }}
        """
        repo_result = github.query(repo_query)

        if "errors" in repo_result:
            return f"Error: Failed to get repository info: {repo_result['errors']}"

        repository_id = repo_result.get("repository", {}).get("id")
        if not repository_id:
            return f"Error: Could not get repository ID for {owner}/{repo}"

        # Build the mutation input
        mutation_input_parts = [
            f'repositoryId: "{repository_id}"',
            f'title: "{title.replace('"', '\\"')}"',
        ]

        if body:
            # Escape special characters in body
            escaped_body = body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            mutation_input_parts.append(f'body: "{escaped_body}"')

        # Get label IDs if labels are specified
        if labels:
            label_query = f"""
            repository(owner: "{owner}", name: "{repo}") {{
                labels(first: 100) {{
                    nodes {{
                        id
                        name
                    }}
                }}
            }}
            """
            label_result = github.query(label_query)
            label_nodes = label_result.get("repository", {}).get("labels", {}).get("nodes", [])
            label_ids = [node["id"] for node in label_nodes if node.get("name") in labels]
            if label_ids:
                label_ids_str = ", ".join([f'"{lid}"' for lid in label_ids])
                mutation_input_parts.append(f"labelIds: [{label_ids_str}]")

        # Get assignee IDs if assignees are specified
        if assignees:
            assignee_ids: list[str] = []
            for assignee in assignees:
                user_query = f"""
                user(login: "{assignee}") {{
                    id
                }}
                """
                user_result = github.query(user_query)
                user_id = user_result.get("user", {}).get("id")
                if user_id:
                    assignee_ids.append(user_id)

            if assignee_ids:
                assignee_ids_str = ", ".join([f'"{aid}"' for aid in assignee_ids])
                mutation_input_parts.append(f"assigneeIds: [{assignee_ids_str}]")

        # Get milestone ID if milestone is specified
        if milestone:
            milestone_query = f"""
            repository(owner: "{owner}", name: "{repo}") {{
                milestones(first: 100) {{
                    nodes {{
                        id
                        title
                    }}
                }}
            }}
            """
            milestone_result = github.query(milestone_query)
            milestone_nodes = milestone_result.get("repository", {}).get("milestones", {}).get("nodes", [])
            milestone_id = None
            for node in milestone_nodes:
                if node.get("title") == milestone:
                    milestone_id = node.get("id")
                    break
            if milestone_id:
                mutation_input_parts.append(f'milestoneId: "{milestone_id}"')

        # Create the issue
        mutation_input = ", ".join(mutation_input_parts)
        create_mutation = f"""
        mutation {{
            createIssue(input: {{{mutation_input}}}) {{
                issue {{
                    id
                    number
                    url
                    title
                }}
            }}
        }}
        """

        result = github.query(create_mutation)

        if "errors" in result:
            return f"Error: Failed to create issue: {result['errors']}"

        issue_data = result.get("createIssue", {}).get("issue")
        if not issue_data:
            return "Error: Issue creation returned no data"

        issue_id = issue_data.get("id")
        issue_number = issue_data.get("number")
        issue_url = issue_data.get("url")
        issue_title = issue_data.get("title")

        # Link to project board if specified
        project_linked = False
        project_item_id = None
        custom_fields_results: dict[str, bool] = {}
        if project_url and issue_id:
            project_id = _get_project_id(project_url, github)
            if project_id:
                project_item_id = _add_issue_to_project(issue_id, project_id, github)
                project_linked = project_item_id is not None
                if project_linked:
                    logger.info(f"Issue #{issue_number} added to project board")

                    # Set custom fields if specified
                    if custom_fields and project_item_id:
                        custom_fields_results = _set_custom_fields_on_item(
                            project_url=project_url,
                            project_id=project_id,
                            item_id=project_item_id,
                            custom_fields=custom_fields,
                            github=github,
                        )
                        for field_name, success in custom_fields_results.items():
                            if success:
                                logger.info(f"Set field '{field_name}' on issue #{issue_number}")
                            else:
                                logger.warning(f"Failed to set field '{field_name}' on issue #{issue_number}")
                else:
                    logger.warning(f"Failed to add issue #{issue_number} to project board")
            else:
                logger.warning(f"Could not find project at {project_url}")

        # Format the output
        output_lines = [
            f"## Issue Created: #{issue_number}",
            f"**Title:** {issue_title}",
            f"**URL:** {issue_url}",
        ]

        if labels:
            output_lines.append(f"**Labels:** {', '.join(labels)}")
        if assignees:
            output_lines.append(f"**Assignees:** {', '.join(assignees)}")
        if milestone:
            output_lines.append(f"**Milestone:** {milestone}")
        if project_url:
            if project_linked:
                output_lines.append(f"**Project:** Linked to {project_url}")
                # Add custom fields status
                if custom_fields_results:
                    successful_fields = [f for f, s in custom_fields_results.items() if s]
                    failed_fields = [f for f, s in custom_fields_results.items() if not s]
                    if successful_fields:
                        output_lines.append(f"**Custom Fields Set:** {', '.join(successful_fields)}")
                    if failed_fields:
                        output_lines.append(f"**Custom Fields Failed:** {', '.join(failed_fields)}")
            else:
                output_lines.append(f"**Project:** Failed to link to {project_url}")

        return "\n".join(output_lines)

    except Exception as e:
        logger.error(f"Error creating issue: {e}")
        return f"Error: {str(e)}"
