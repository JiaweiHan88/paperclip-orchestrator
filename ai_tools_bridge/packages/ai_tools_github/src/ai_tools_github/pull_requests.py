from typing import cast

from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github

from .models.pull_request import (
    PULL_REQUEST_GRAPHQL_QUERY,
    PullRequest,
    pull_request_list_to_markdown,
    pull_request_to_markdown,
)


class PullRequestInput(BaseModel):
    """Input model for getting information of a github pull request."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["swh", "software-factory"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo1", "xpad-shared"],
    )
    number: int = Field(
        description="The number of the pull request.",
        examples=[134, 83733],
    )


class UpdatePullRequestDescriptionInput(BaseModel):
    """Input model for updating a pull request description."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["swh", "software-factory"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo1", "xpad-shared"],
    )
    number: int = Field(
        description="The number of the pull request.",
        examples=[134, 83733],
    )
    body: str = Field(
        description="The new description for the pull request.",
        examples=["Updated description with new information."],
    )


class AddToPullRequestDescriptionInput(BaseModel):
    """Input model for adding a section to a pull request description."""

    pr_node_id: str = Field(
        description="The node ID of the pull request.",
        examples=["PR_kwDOABCDE123456789"],
    )
    injection_title: str = Field(
        description="The title for the injected section.",
        examples=["Summary", "Analysis Results"],
    )
    start_keyword: str = Field(
        description="The keyword marking the start of the injection section.",
        examples=["<!-- summary-start -->", "<!-- analysis-start -->"],
    )
    end_keyword: str = Field(
        description="The keyword marking the end of the injection section.",
        examples=["<!-- summary-end -->", "<!-- analysis-end -->"],
    )
    description_old: str = Field(
        description="The current description of the pull request.",
        examples=["This PR implements new feature X."],
    )
    injection_text: str = Field(
        description="The text to inject into the section.",
        examples=["This is the summary content.", "Analysis completed successfully."],
    )


def get_pull_request(
    owner: str,
    repo: str,
    number: int,
    github: Github,
) -> str:
    """Get information about a pull request.

    Retrieves comprehensive details about a pull request including title,
    description, author, status, and review information.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        number: The number of the pull request.
        github: GitHub instance for API access.

    Returns:
        Markdown formatted string with pull request details.

    Raises:
        Exception: If the pull request does not exist or access is denied.
    """
    pull_request = cast(
        PullRequest,
        github.pull_request(
            owner=owner,
            repo=repo,
            number=number,
            querydata=PULL_REQUEST_GRAPHQL_QUERY,
            instance_class=PullRequest,  # pyright: ignore
        ),
    )

    text = pull_request_to_markdown(pull_request)

    return text


def get_pull_request_structured(
    owner: str,
    repo: str,
    number: int,
    github: Github,
) -> PullRequest:
    """Get structured information about a pull request.

    Retrieves comprehensive details about a pull request as a structured
    PullRequest object for programmatic access.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        number: The number of the pull request.
        github: GitHub instance for API access.

    Returns:
        PullRequest object with all pull request details.

    Raises:
        Exception: If the pull request does not exist or access is denied.
    """
    pull_request = cast(
        PullRequest,
        github.pull_request(
            owner=owner,
            repo=repo,
            number=number,
            querydata=PULL_REQUEST_GRAPHQL_QUERY,
            instance_class=PullRequest,  # pyright: ignore
        ),
    )

    return pull_request


def update_pull_request_description(
    owner: str,
    repo: str,
    number: int,
    body: str,
    github: Github,
) -> str:
    """Update the description of a pull request.

    Replaces the entire body/description of a pull request with new content.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        number: The number of the pull request.
        body: The new description for the pull request.
        github: GitHub instance for API access.

    Returns:
        Confirmation message with PR number and repository.

    Raises:
        ValueError: If the pull request ID cannot be retrieved.
        Exception: If the update operation fails.
    """
    pr = github.pull_request(owner, repo, number, querydata="id")

    if pr.id is None:
        msg = f"Could not get ID for PR #{number} in {owner}/{repo}"
        raise ValueError(msg)

    github.update_pull_request(
        pull_request_id=pr.id,
        body=body,
    )

    return f"Successfully updated description for PR #{number} in {owner}/{repo}"


def inject_to_pull_request_description(
    pr_node_id: str,
    injection_title: str,
    start_keyword: str,
    end_keyword: str,
    description_old: str,
    injection_text: str,
    github: Github,
) -> None:
    """Inject a collapsible section into the pull request description.

    Inserts or updates a collapsible section in the PR description between
    the specified start and end keywords. If the section already exists,
    it will be replaced with the new content.

    Args:
        pr_node_id: The node ID of the pull request.
        injection_title: The title for the injected collapsible section.
        start_keyword: The keyword marking the start of the injection section.
        end_keyword: The keyword marking the end of the injection section.
        description_old: The current description of the pull request.
        injection_text: The text to inject into the section.
        github: GitHub instance for API access.

    Raises:
        Exception: If the update operation fails.
    """

    def create_collapsible_summary(include_leading_newline: bool = False) -> str:
        leading_newline = "\n" if include_leading_newline else ""
        return (
            f"{leading_newline}{start_keyword}\n"
            f"<details>\n"
            f"<summary>{injection_title}</summary>\n\n"
            f"{injection_text}\n\n"
            f"</details>\n"
            f"{end_keyword}"
        )

    start_index = description_old.find(start_keyword)

    if start_index != -1:
        search_start = start_index + len(start_keyword)
        end_index = description_old.find(end_keyword, search_start)
        before_section = description_old[:start_index]

        if end_index != -1:
            after_section = description_old[end_index + len(end_keyword) :]
            description = f"{before_section}{create_collapsible_summary()}{after_section}"
        else:
            description = f"{before_section}{create_collapsible_summary()}"
    else:
        collapsible_summary = create_collapsible_summary(include_leading_newline=True)
        if description_old.strip():
            description = f"{description_old}\n\n---{collapsible_summary}"
        else:
            description = f"---{collapsible_summary}"

    github.update_pull_request(
        pull_request_id=pr_node_id,
        body=description,
    )


class SearchPullRequestsInput(BaseModel):
    query: str = Field(
        description="The search query to find pull requests.",
        examples=[
            "repo:software-factory/repo1 is:pr is:open author:someuser",
            "repo:swh/repo2 is:pr is:closed label:bug",
        ],
    )


def search_pull_requests(
    query: str,
    github: Github,
) -> str:
    """
    Search for pull requests based on a query.

    Args:
        query (str): The search query.

    Returns:
        list[dict]: A list of pull request data dictionaries.
    """
    pull_requests = cast(
        list[PullRequest],
        github.search_pull_requests(
            search_query=query,
            querydata=PULL_REQUEST_GRAPHQL_QUERY,
            instance_class=PullRequest,  # pyright: ignore
        ),
    )

    return pull_request_list_to_markdown(pull_requests)
