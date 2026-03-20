"""Tool for retrieving repository statistics and metadata information."""

from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github


class RepoStatsInput(BaseModel):
    """Input model for getting statistics and metadata information of a repository."""

    owner: str = Field(
        description="The owner of the GitHub repository.",
        examples=["octocat", "microsoft", "tensorflow"],
    )
    repo: str = Field(
        description="The name of the GitHub repository.",
        examples=["Hello-World", "vscode", "tensorflow"],
    )


def is_bot_author(login: str) -> bool:
    """Check if an author login indicates a bot account."""
    bot_patterns = [
        "bot",
        "dependabot",
        "github-actions",
        "renovate",
        "zuul[bot]",
        "codecov",
        "greenkeeper",
        "snyk-bot",
    ]

    login_lower = login.lower()
    return any(pattern in login_lower for pattern in bot_patterns) or login_lower.endswith("[bot]")


def get_repo_stats(owner: str, repo: str, github: Github) -> str:
    """
    Retrieve comprehensive statistics and metadata for a repository.

    This function provides a complete overview of repository health and activity,
    including development metrics, contributor analysis, and project metadata.
    The tool is essential for understanding repository status, activity levels,
    and community engagement.

    Features included:
    - Basic repository information (description, creation date, status)
    - Development metrics (stars, forks, watchers, issues, pull requests)
    - Language and technology stack analysis
    - Contributor statistics and top contributors
    - Release information and licensing details
    - Repository size and storage usage

    Args:
        owner: The owner of the GitHub repository (username or organization)
        repo: The name of the GitHub repository
        github: GitHub instance for API access

    Returns:
        Comprehensive markdown-formatted report containing:
        - Repository metadata and status information
        - Activity metrics and statistics
        - Technology stack and programming languages
        - Contributor analysis with commit counts
        - Project health indicators

    Raises:
        Exception: If the repository cannot be accessed or statistics cannot be retrieved
    """
    try:
        # GraphQL query to get comprehensive repository metadata and statistics
        repo_query = (
            f'repository(owner: "{owner}", name: "{repo}") {{ '
            "name url description createdAt updatedAt "
            "stargazerCount forkCount watchers { totalCount } "
            "primaryLanguage { name } "
            "languages(first: 20, orderBy: {field: SIZE, direction: DESC}) { "
            "nodes { name } } "
            "repositoryTopics(first: 20) { nodes { topic { name } } } "
            "defaultBranchRef { "
            "name "
            "target { "
            "... on Commit { "
            "history(first: 100) { "
            "totalCount "
            "nodes { "
            "author { name email user { login } } "
            "} } } } } "
            "diskUsage "
            "isPrivate isArchived isFork "
            "licenseInfo { name spdxId url } "
            "openIssues: issues(states: OPEN) { totalCount } "
            "closedIssues: issues(states: CLOSED) { totalCount } "
            "openPullRequests: pullRequests(states: OPEN) { totalCount } "
            "closedPullRequests: pullRequests(states: CLOSED) { totalCount } "
            "mergedPullRequests: pullRequests(states: MERGED) { totalCount } "
            "releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) { "
            "nodes { name createdAt tagName } "
            "} "
            "} }"
        )

        result = github.query(repo_query)

        if "errors" in result:
            logger.error(f"GraphQL errors: {result['errors']}")
            return f"Error fetching repository data: {result['errors']}"

        repo_data = result.get("repository")
        if not repo_data:
            return "Repository not found or access denied."

        output_lines: list[str] = []

        # Repository metadata
        output_lines.append(f"# Repository Statistics: {repo_data['name']}")
        output_lines.append(f"**URL:** {repo_data['url']}")

        description = repo_data.get("description")
        if description:
            output_lines.append(f"**Description:** {description}")
        else:
            output_lines.append("**Description:** No description")

        output_lines.append(f"**Created:** {repo_data['createdAt'].replace('T', ' ').replace('Z', '')}")
        output_lines.append(f"**Last Updated:** {repo_data['updatedAt'].replace('T', ' ').replace('Z', '')}")

        # Repository status
        status_info: list[str] = []
        if repo_data.get("isPrivate"):
            status_info.append("Private")
        else:
            status_info.append("Public")

        if repo_data.get("isArchived"):
            status_info.append("Archived")

        if repo_data.get("isFork"):
            status_info.append("Fork")

        output_lines.append(f"**Status:** {', '.join(status_info)}")
        output_lines.append("")

        # Repository statistics
        output_lines.append("## Repository Statistics")
        output_lines.append(f"**Stars:** {repo_data['stargazerCount']:,}")
        output_lines.append(f"**Forks:** {repo_data['forkCount']:,}")
        output_lines.append(f"**Watchers:** {repo_data['watchers']['totalCount']:,}")

        # Issues and Pull Requests
        open_issues = repo_data.get("openIssues", {}).get("totalCount", 0)
        closed_issues = repo_data.get("closedIssues", {}).get("totalCount", 0)
        total_issues = open_issues + closed_issues

        open_prs = repo_data.get("openPullRequests", {}).get("totalCount", 0)
        closed_prs = repo_data.get("closedPullRequests", {}).get("totalCount", 0)
        merged_prs = repo_data.get("mergedPullRequests", {}).get("totalCount", 0)
        total_prs = open_prs + closed_prs + merged_prs

        output_lines.append(f"**Issues:** {open_issues:,} open, {closed_issues:,} closed ({total_issues:,} total)")
        output_lines.append(
            f"**Pull Requests:** {open_prs:,} open, {merged_prs:,} merged, {closed_prs:,} closed ({total_prs:,} total)"
        )

        # Commits
        default_branch = repo_data.get("defaultBranchRef", {})
        if default_branch and default_branch.get("target"):
            commit_history = default_branch["target"].get("history", {})
            total_commits = commit_history.get("totalCount", 0)
            output_lines.append(f"**Total Commits:** {total_commits:,}")
            output_lines.append(f"**Default Branch:** {default_branch['name']}")

        # Languages
        primary_lang = repo_data.get("primaryLanguage", {})
        if primary_lang:
            output_lines.append(f"**Primary Language:** {primary_lang['name']}")

        languages = [lang["name"] for lang in repo_data.get("languages", {}).get("nodes", [])]
        if languages:
            output_lines.append(f"**Languages:** {', '.join(languages)}")

        # Topics/Tags
        topics = [topic["topic"]["name"] for topic in repo_data.get("repositoryTopics", {}).get("nodes", [])]
        if topics:
            output_lines.append(f"**Topics:** {', '.join(topics)}")

        # License
        license_info = repo_data.get("licenseInfo")
        if license_info:
            output_lines.append(f"**License:** {license_info['name']} ({license_info.get('spdxId', 'N/A')})")

        # Repository size
        if repo_data.get("diskUsage"):
            disk_usage_mb = repo_data["diskUsage"] / 1024  # Convert KB to MB
            if disk_usage_mb >= 1024:
                disk_usage_gb = disk_usage_mb / 1024
                output_lines.append(f"**Repository Size:** {disk_usage_gb:.2f} GB")
            else:
                output_lines.append(f"**Repository Size:** {disk_usage_mb:.2f} MB")

        # Latest release
        releases = repo_data.get("releases", {}).get("nodes", [])
        if releases:
            latest_release = releases[0]
            release_date = latest_release["createdAt"].replace("T", " ").replace("Z", "")
            output_lines.append(
                f"**Latest Release:** {latest_release['name']} ({latest_release['tagName']}) - {release_date}"
            )

        output_lines.append("")

        # Contributors analysis
        output_lines.append("## Contributors")

        # Get contributors from commits
        contributors: dict[str, dict[str, Any]] = {}
        if default_branch and default_branch.get("target"):
            commit_history = default_branch["target"].get("history", {})
            commits = commit_history.get("nodes", [])

            for commit in commits:
                author_info = commit.get("author", {})
                author_name = author_info.get("name", "Unknown")
                author_user = author_info.get("user", {})
                author_login = author_user.get("login") if author_user else None

                if author_login and not is_bot_author(author_login):
                    if author_login not in contributors:
                        contributors[author_login] = {"name": author_name, "commits": 0}
                    contributors[author_login]["commits"] += 1

        if contributors:
            # Sort contributors by commit count
            sorted_contributors = sorted(contributors.items(), key=lambda x: x[1]["commits"], reverse=True)
            output_lines.append(f"**Total Contributors:** {len(contributors)}")
            output_lines.append("")
            output_lines.append("**Top Contributors (by commits):**")

            for i, (login, data) in enumerate(sorted_contributors[:10], 1):  # Show top 10
                name = data["name"]
                commit_count = data["commits"]
                if name and name != login:
                    output_lines.append(f"{i:2d}. {login} ({name}) - {commit_count} commits")
                else:
                    output_lines.append(f"{i:2d}. {login} - {commit_count} commits")

            if len(sorted_contributors) > 10:
                output_lines.append(f"    ... and {len(sorted_contributors) - 10} more contributors")
        else:
            output_lines.append("No contributors data available")

        output_lines.append("")

        md_output = "\n".join(output_lines)
        return md_output

    except Exception as e:
        logger.error(f"Error fetching repository statistics: {e}")
        return f"Error: {str(e)}"
