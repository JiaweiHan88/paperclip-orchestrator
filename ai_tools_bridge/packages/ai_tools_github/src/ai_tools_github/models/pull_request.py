from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from ai_tools_github.github_base import GraphQlModel


class Author(GraphQlModel):
    """Author of a pull request, review, or comment."""

    login: str


class User(GraphQlModel):
    """User information."""

    login: str


class Team(GraphQlModel):
    """Team information."""

    name: str


class Repository(GraphQlModel):
    """Repository information."""

    name: str
    name_with_owner: str


class Label(GraphQlModel):
    """Label information."""

    name: str
    color: str


class Participant(GraphQlModel):
    """Participant in a pull request."""

    login: str


class Comment(GraphQlModel):
    """Comment on a pull request."""

    author: Author
    body: str
    created_at: datetime


class Review(GraphQlModel):
    """Pull request review."""

    author: Author
    state: str
    created_at: datetime
    body: str
    id: str


class CheckRun(GraphQlModel):
    """Check run status check."""

    name: str | None = None
    status: str | None = None
    conclusion: str | None = None
    summary: str | None = None
    completed_at: datetime | None = None


class StatusContext(GraphQlModel):
    """Status context status check."""

    context: str | None = None
    state: str | None = None


StatusCheckContext = CheckRun | StatusContext


class StatusCheckRollup(GraphQlModel):
    """Status check rollup for a commit.

    Note: The 'contexts' field will be automatically unwrapped from 'contexts.nodes'
    by the base class unwrap_nodes validator.
    """

    contexts: list[StatusCheckContext] = Field(default_factory=list[StatusCheckContext])


class Commit(GraphQlModel):
    """Commit information."""

    message_headline: str = ""
    message_body: str = ""
    oid: str = ""
    committed_date: datetime | None = None
    status_check_rollup: StatusCheckRollup | None = None

    @model_validator(mode="before")
    @classmethod
    def prep_commit_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Prep Commit Data

        Args:
            data (dict): The to be validated input data

        Returns:
            dict: The valiated and transformed input data
        """

        if "statusCheckRollup" in data and data["statusCheckRollup"]:
            if "contexts" in data["statusCheckRollup"]:
                data["statusCheckRollup"]["contexts"] = data["statusCheckRollup"]["contexts"]["nodes"]

        return data


class MergeCommit(GraphQlModel):
    """Merge commit information."""

    oid: str
    committed_date: datetime


RequestedReviewer = User | Team


class ReviewRequest(GraphQlModel):
    """Pull request review."""

    as_code_owner: bool
    requested_reviewer: RequestedReviewer | None


class PullRequest(GraphQlModel):
    """Pull request with all required fields from the GraphQL query.

    Note: Collection fields (reviews, labels, participants, comments, commits)
    are automatically unwrapped from their 'nodes' wrapper by the base class
    unwrap_nodes validator. The commits field also has individual commit objects
    extracted from their wrapper nodes.
    """

    number: int | None = None
    title: str | None = None
    body: str | None = None
    base_ref_name: str | None = None
    head_ref_name: str | None = None
    head_ref_oid: str | None = None
    url: str | None = None
    id: str | None = None

    closed: bool = False
    merged: bool = False
    is_draft: bool = False
    mergeable: str | None = None
    merge_commit: MergeCommit | None = None

    review_decision: str | None = None

    additions: int = 0
    deletions: int = 0

    # These are unwrapped from { nodes: [...] } to [...] automatically
    reviews: list[Review] = Field(default_factory=list[Review])
    review_requests: list[ReviewRequest] = Field(default_factory=list[ReviewRequest])
    labels: list[Label] = Field(default_factory=list[Label])
    participants: list[Participant] = Field(default_factory=list[Participant])

    # Author and repository are direct objects
    author: Author | None = None
    repository: Repository | None = None

    # Comments has totalCount alongside nodes, so we keep the wrapper
    comments: list[Comment] = Field(default_factory=list[Comment])

    # Commits needs special handling - see validator below
    commits: list[Commit] = Field(default_factory=list[Commit])

    @property
    def uri(self) -> str:
        """Returns the uri of the pull request.

        Returns:
            str: The uri of the pull request (e.g., "owner/repo#123")
        """
        assert self.repository is not None, "Repository must be set to get URI"
        return f"{self.repository.name_with_owner}#{self.number}"

    @model_validator(mode="before")
    @classmethod
    def prep_pull_request_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Prep Pull Request Data

        Args:
            data (dict): The to be validated input data

        Returns:
            dict: The valiated and transformed input data
        """

        if "commits" in data:
            if "nodes" in data["commits"]:
                data["commits"] = data["commits"]["nodes"]

            data["commits"] = [x["commit"] if "commit" in x else x for x in data["commits"]]

        return data


PULL_REQUEST_GRAPHQL_QUERY = """
number
title
body
baseRefName
headRefName
headRefOid
url
id

closed
merged
isDraft
mergeable
mergeCommit { oid committedDate }

reviewDecision

additions
deletions

reviewRequests (last: 100) {
    nodes {
        asCodeOwner
        requestedReviewer {
            ... on User {
                login
            }
            ... on Team {
                name
            }
        }
    }
}

reviews (last: 100) {
    nodes {
        author { login }
        state
        createdAt
        body
        id
    }
}

author { login }

repository { name nameWithOwner }

labels (first:10) { nodes { name color } }

participants (last: 100) {
    nodes {
        login
    }
}

comments (last: 100) {
    totalCount
    nodes {
        author { login }
        body
        createdAt
    }
}

commits (last: 50) {
    totalCount
    nodes {
        commit {
            messageHeadline
            messageBody
            oid

            statusCheckRollup {
                contexts (last: 50) {
                    nodes {
                        ... on CheckRun {
                            name
                            status
                            conclusion
                            summary
                            completedAt
                        }
                        ... on StatusContext {
                            context
                            state
                        }
                    }
                }
            }
        }
    }
}
"""


def pull_request_to_markdown(pull_request: PullRequest) -> str:
    """Convert a PullRequest object to a Markdown string."""

    review_state = pull_request.review_decision or "UNREVIEWED"
    mergeable_state = pull_request.mergeable or "UNKNOWN"
    status = "open " + review_state + " " + mergeable_state
    if pull_request.merged:
        assert pull_request.merge_commit is not None, "Merge commit should be present for merged pull requests"
        status = f"merged ({pull_request.merge_commit.oid})"
    elif pull_request.closed:
        status = "closed"

    markdown = f"# [{pull_request.uri}] {pull_request.title} ({status.capitalize()})\n\n"
    markdown += f"{pull_request.base_ref_name} <- {pull_request.head_ref_name}\n\n"
    markdown += f"{pull_request.body}\n\n"
    markdown += f"Labels: {', '.join(label.name for label in pull_request.labels)}\n\n"

    # Reviews section
    markdown += "## Reviews:\n"
    if pull_request.reviews:
        for review in pull_request.reviews:
            markdown += f"**{review.author.login}** ({review.state}) at {review.created_at}:\n"
            if review.body:
                markdown += f"{review.body}\n"
            markdown += "\n"
    else:
        markdown += f"No reviews (Review Decision: {pull_request.review_decision or 'UNREVIEWED'})\n\n"

    # Requested Reviews section
    markdown += "## Requested Reviews:\n"
    valid_review_requests = [rr for rr in pull_request.review_requests if rr.requested_reviewer is not None]
    if valid_review_requests:
        for review_request in valid_review_requests:
            reviewer = review_request.requested_reviewer
            if reviewer is None:
                continue
            if isinstance(reviewer, User):
                reviewer_name = reviewer.login
            else:  # Team
                reviewer_name = reviewer.name
            code_owner_tag = " (Code Owner)" if review_request.as_code_owner else ""
            markdown += f"- {reviewer_name}{code_owner_tag}\n"
        markdown += "\n"
    else:
        markdown += "No review requests\n\n"

    # Status Checks section
    markdown += "## Status Checks:\n"
    if pull_request.commits:
        last_commit = pull_request.commits[-1]
        if last_commit.status_check_rollup and last_commit.status_check_rollup.contexts:
            for context in last_commit.status_check_rollup.contexts:
                if isinstance(context, CheckRun):
                    conclusion = f" - {context.conclusion}" if context.conclusion else ""
                    markdown += f"- **{context.name}**: {context.status}{conclusion}\n"
                else:  # StatusContext
                    markdown += f"- **{context.context}**: {context.state}\n"
            markdown += "\n"
        else:
            markdown += "No CI checks\n\n"
    else:
        markdown += "No CI checks\n\n"

    markdown += "## Comments:\n"
    for comment in pull_request.comments:
        markdown += f"{comment.author.login}:\n{comment.body}\n\n"

    return markdown


def pull_request_list_to_markdown(pull_requests: list[PullRequest]) -> str:
    """Convert a list of PullRequest objects to a Markdown string."""
    return "\n".join(f"- [{pr.uri}] {pr.title}" for pr in pull_requests)
