import re
from typing import Any

from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github
from ai_tools_github.models.pull_request import CheckRun, PullRequest

# GraphQL query to fetch pull request with status checks
BUILDSET_PR_QUERY = """
commits (last: 1) {
    nodes {
        commit {
            statusCheckRollup {
                contexts (last: 100) {
                    nodes {
                        ... on CheckRun {
                            name
                            status
                            conclusion
                            summary
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


class FetchZuulBuildsetsInput(BaseModel):
    """Input model for fetching buildsets from a GitHub repository."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["example-org", "example-user"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["example-repo"],
    )

    number: int = Field(
        description="The pull request ID to fetch buildsets for.",
        examples=[42],
    )


class ZuulCheckRun(BaseModel):
    """Structure for a Zuul buildset."""

    pipeline: str = Field(description="The name of the pipeline.")
    buildset_id: str = Field(description="The ID of the buildset.")
    tenant: str = Field(
        description="The tenant associated with the buildset.",
    )
    status: str = Field(
        description="The status of the buildset.",
    )
    conclusion: str = Field(
        description="The conclusion of the buildset.",
    )
    summary: str = Field(
        description="The summary information of the buildset.",
    )


class FetchZuulBuildsetsOutput(BaseModel):
    """Output model for fetched Zuul buildsets."""

    buildsets: list[ZuulCheckRun] = Field(
        description="List of Zuul buildsets associated with the pull request.",
        default_factory=list[ZuulCheckRun],
    )


def get_zuul_buildsets_for_pr(
    owner: str,
    repo: str,
    number: int,
    github: Github,
) -> FetchZuulBuildsetsOutput:  # TODO Parsing will be part of tool-postprocessing in the future
    """Fetch Zuul buildsets associated with a pull request.

    Retrieves all Zuul buildset information from the status checks on a pull
    request. Parses Zuul-specific check runs to extract pipeline names, buildset
    IDs, and tenant information.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.
        number: The pull request number to fetch buildsets for.
        github: GitHub instance for API access.

    Returns:
        FetchZuulBuildsetsOutput containing the list of Zuul buildsets with their
        pipeline information, status, and conclusion.

    Raises:
        Exception: If the pull request does not exist or access is denied.
    """
    # Fetch the pull request with status check information
    pull_request = github.pull_request(
        owner=owner,
        repo=repo,
        number=number,
        querydata=BUILDSET_PR_QUERY,
        instance_class=PullRequest,
    )

    buildsets: list[dict[str, Any]] = []

    # Extract buildsets from the latest commit's status checks
    if pull_request.commits:
        last_commit = pull_request.commits[-1]
        if last_commit.status_check_rollup and last_commit.status_check_rollup.contexts:
            for context in last_commit.status_check_rollup.contexts:
                # Only process CheckRun contexts for Zuul buildsets
                if isinstance(context, CheckRun):
                    buildset_info = _extract_zuul_buildset_from_check_run(context)
                    if buildset_info:
                        buildsets.append(buildset_info)

    return FetchZuulBuildsetsOutput(
        buildsets=[
            ZuulCheckRun(
                pipeline=bs["pipeline"],
                buildset_id=bs.get("buildset_id") or "",
                tenant=bs.get("tenant") or "",
                status=bs.get("status") or "",
                conclusion=bs.get("conclusion") or "",
                summary=bs.get("summary") or "",
            )
            for bs in buildsets
        ]
    )


def _extract_zuul_buildset_from_check_run(check_run: CheckRun) -> dict[str, Any] | None:
    """
    Extract Zuul buildset information from a GitHub check run.

    Args:
        check_run: The GitHub check run to extract Zuul buildset information from.

    Returns:
        Dictionary containing Zuul buildset information or None if not a Zuul buildset.
    """
    # Only process check runs with names
    if not check_run.name:
        return None

    # Only process Zuul check runs (check for zuul in name or summary)
    is_zuul = False
    if "zuul" in check_run.name.lower():
        is_zuul = True
    elif check_run.summary and "zuul" in check_run.summary.lower():
        is_zuul = True

    if not is_zuul:
        return None

    buildset_info = {
        "pipeline": check_run.name,
        "type": "zuul_check_run",
        "status": check_run.status if check_run.status else None,
        "conclusion": check_run.conclusion if check_run.conclusion else None,
        "summary": check_run.summary,
    }

    # Try to extract buildset ID and tenant from the summary
    if check_run.summary:
        # Look for buildset ID pattern
        id_match = re.search(r"buildset[/\\](\w+)", check_run.summary)
        if id_match:
            buildset_info["buildset_id"] = id_match.group(1)

        # Look for tenant information
        tenant_match = re.search(r"zuul[/\\]t[/\\](\w+)", check_run.summary)
        if tenant_match:
            buildset_info["tenant"] = tenant_match.group(1)

    return buildset_info
