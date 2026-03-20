"""Tool for retrieving comprehensive repository history with timeline information."""

from datetime import datetime

from loguru import logger
from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github


class RepoHistoryInput(BaseModel):
    """Input model for getting commit timeline history of a repository."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["owner", "some-user"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo", "some-repo"],
    )
    limit: int = Field(
        default=50,
        description="Maximum number of commits to retrieve for timeline (default: 50, max: 500).",
        examples=[25, 50, 100],
    )
    from_timestamp: str | None = Field(
        default=None,
        description="Optional ISO timestamp to filter timeline events from (inclusive, e.g., '2025-11-18T20:18:55Z').",
        examples=["2025-11-18T20:18:55Z"],
    )
    to_timestamp: str | None = Field(
        default=None,
        description="Optional ISO timestamp to filter timeline events to (inclusive, e.g., '2025-11-20T20:18:55Z').",
        examples=["2025-11-20T20:18:55Z"],
    )
    file_scope: list[str] | None = Field(
        default=None,
        description=(
            "Optional list of file extensions or patterns to include in diffs "
            "(e.g., ['.py', '.js', '.md']). If not specified, includes all files "
            "except common binary and lock files."
        ),
        examples=[[".py", ".js"], [".md", ".txt"], [".yaml", ".yml", ".json"]],
    )


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime object."""
    # Handle both with and without timezone info
    if timestamp_str.endswith("Z"):
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    return datetime.fromisoformat(timestamp_str)


def should_include_commit(
    commit_time: str,
    from_timestamp: str | None = None,
    to_timestamp: str | None = None,
) -> bool:
    """Check if commit should be included based on timestamp filters.

    Args:
        commit_time: ISO timestamp string of the commit
        from_timestamp: Optional start timestamp (inclusive)
        to_timestamp: Optional end timestamp (inclusive)

    Returns:
        True if commit should be included, False otherwise
    """
    if not from_timestamp and not to_timestamp:
        return True

    commit_dt = parse_timestamp(commit_time)

    # Check from_timestamp (inclusive)
    if from_timestamp:
        from_dt = parse_timestamp(from_timestamp)
        if commit_dt < from_dt:
            return False

    # Check to_timestamp (inclusive)
    if to_timestamp:
        to_dt = parse_timestamp(to_timestamp)
        if commit_dt > to_dt:
            return False

    return True


def format_diff_stats(additions: int, deletions: int) -> str:
    """Format diff statistics in a readable way."""
    total_changes = additions + deletions
    if total_changes == 0:
        return "No changes"
    return f"+{additions} -{deletions} ({total_changes} total changes)"


def get_repo_history(
    owner: str,
    repo: str,
    github: Github,
    limit: int = 50,
    from_timestamp: str | None = None,
    to_timestamp: str | None = None,
    file_scope: list[str] | None = None,
) -> str:
    """
    Retrieve comprehensive commit timeline history for a repository.

    This function provides a detailed timeline of repository commits, including
    author information, commit messages, diff statistics, and associated pull requests.
    The timeline can be filtered by date range and file scope to focus on specific
    changes. This tool is essential for understanding repository evolution and
    tracking development progress.

    Args:
        owner: Repository owner (GitHub username or organization)
        repo: Repository name
        github: GitHub instance for API access
        limit: Maximum number of commits to retrieve (default: 50, max recommended: 500)
        from_timestamp: Optional ISO timestamp to filter from (inclusive, e.g., '2025-11-18T20:18:55Z')
        to_timestamp: Optional ISO timestamp to filter to (inclusive, e.g., '2025-11-20T20:18:55Z')
        file_scope: Optional list of file extensions to focus on (e.g., ['.py', '.js', '.md'])

    Returns:
        Formatted markdown string with chronological commit timeline including:
        - Commit metadata (author, timestamp, SHA)
        - Commit messages and diff statistics
        - Associated pull request information
        - Suggestions for detailed diff analysis

    Raises:
        Exception: If the repository cannot be accessed or commit history cannot be retrieved
    """
    try:
        # GraphQL query to get repository commit history
        repo_query = (
            f'repository(owner: "{owner}", name: "{repo}") {{ '
            "name url "
            "defaultBranchRef { "
            "name "
            "target { "
            "... on Commit { "
            f"history(first: {limit}) {{ "
            "totalCount "
            "nodes { "
            "oid message committedDate "
            "author { name email user { login } } "
            "additions deletions "
            "associatedPullRequests(first: 1) { nodes { number title url } } "
            "} } } } } "
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

        # Repository header
        output_lines.append(f"# Repository History: {repo_data['name']}")
        output_lines.append(f"**URL:** {repo_data['url']}")

        if file_scope:
            output_lines.append(f"**File Scope:** {', '.join(file_scope)}")

        # Show date range filter if applied
        date_filter_parts: list[str] = []
        if from_timestamp:
            date_filter_parts.append(f"from {from_timestamp}")
        if to_timestamp:
            date_filter_parts.append(f"to {to_timestamp}")
        if date_filter_parts:
            output_lines.append(f"**Date Filter:** {' '.join(date_filter_parts)}")

        output_lines.append("")

        # Timeline of commits
        default_branch = repo_data.get("defaultBranchRef", {})
        if default_branch and default_branch.get("target"):
            commit_history = default_branch["target"].get("history", {})
            total_commits = commit_history.get("totalCount", 0)
            commits = commit_history.get("nodes", [])

            output_lines.append(f"## Timeline ({total_commits:,} total commits)")
            output_lines.append(f"**Default Branch:** {default_branch['name']}")
            output_lines.append("")

            # Filter and display commits
            timeline_events: list[tuple[str, str, str, str, str, str, str]] = []

            for commit in commits:
                commit_date = commit.get("committedDate", "")

                if not should_include_commit(commit_date, from_timestamp, to_timestamp):
                    continue

                timestamp = commit_date.replace("T", " ").replace("Z", "")
                commit_sha = commit["oid"]
                short_sha = commit_sha[:8]
                message = commit.get("message", "").split("\n")[0]  # First line only

                # Author info
                author_info = commit.get("author", {})
                author_name = author_info.get("name", "Unknown")
                author_user = author_info.get("user", {})
                author_login = author_user.get("login") if author_user else None

                if author_login:
                    author_display = f"{author_name} (@{author_login})"
                else:
                    author_display = author_name

                # Diff stats
                additions = commit.get("additions", 0)
                deletions = commit.get("deletions", 0)
                diff_stats = format_diff_stats(additions, deletions)

                # Associated PR info
                pr_info = ""
                associated_prs = commit.get("associatedPullRequests", {}).get("nodes", [])
                if associated_prs:
                    pr = associated_prs[0]  # Take first PR if multiple
                    pr_info = f" (PR #{pr['number']}: {pr['title'][:50]}{'...' if len(pr['title']) > 50 else ''})"

                timeline_events.append(
                    (commit_date, timestamp, short_sha, message, author_display, diff_stats, pr_info)
                )

            # Sort by commit date (most recent first)
            timeline_events.sort(key=lambda x: x[0], reverse=True)

            # Display timeline
            for _, timestamp, short_sha, message, author_display, diff_stats, pr_info in timeline_events:
                output_lines.append(f"**{timestamp}** - `{short_sha}` by {author_display}")
                output_lines.append(f"  {message}")
                output_lines.append(f"  {diff_stats}{pr_info}")
                output_lines.append(f"  Use commit_diff tool with SHA `{short_sha}` to see detailed changes")
                output_lines.append("")

        else:
            output_lines.append("## Timeline")
            output_lines.append("No commit history available (empty repository or access denied)")
            output_lines.append("")

        md_output = "\n".join(output_lines)
        return md_output

    except Exception as e:
        logger.error(f"Error fetching repository history: {e}")
        return f"Error: {str(e)}"
