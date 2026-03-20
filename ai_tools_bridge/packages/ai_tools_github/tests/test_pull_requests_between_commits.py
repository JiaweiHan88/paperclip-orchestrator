"""Test the pull_requests_between_commits functionality."""

from datetime import datetime
from unittest.mock import Mock

from ai_tools_github.pull_requests_between_commits import (
    PullRequestsBetweenCommitsInput,
    get_pull_requests_between_commits,
)


def test_pull_requests_between_commits_input_validation():
    """Test that the input model validates correctly."""
    input_data = PullRequestsBetweenCommitsInput(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="def456",
    )

    assert input_data.owner == "test-owner"
    assert input_data.repo == "test-repo"
    assert input_data.branch == "main"
    assert input_data.start_commit_hash == "abc123"
    assert input_data.end_commit_hash == "def456"


def test_get_pull_requests_between_commits_no_results(mocker):
    """Test the function when no pull requests are found."""
    # Create datetime objects for commit dates
    start_date = datetime(2023, 1, 1, 12, 0, 0)
    end_date = datetime(2023, 1, 2, 12, 0, 0)

    # Mock the Github instance
    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = [
        Mock(oid="abc123", committed_date=start_date),
        Mock(oid="def456", committed_date=end_date),
    ]
    mock_github_instance.search_pull_requests.return_value = []

    result = get_pull_requests_between_commits(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="def456",
        github=mock_github_instance,
    )

    assert "No pull requests found" in result
    assert "test-owner/test-repo" in result


def test_get_pull_requests_between_commits_with_results(mocker):
    """Test the function when pull requests are found."""
    # Mock pull request objects
    mock_pr1 = Mock()
    mock_pr1.url = "https://github.com/test-owner/test-repo/pull/123"
    mock_pr1.uri = "test-owner/test-repo#123"
    mock_pr1.title = "Test PR 1"

    mock_pr2 = Mock()
    mock_pr2.url = "https://github.com/test-owner/test-repo/pull/124"
    mock_pr2.uri = "test-owner/test-repo#124"
    mock_pr2.title = "Test PR 2"

    # Create datetime objects for commit dates
    start_date = datetime(2023, 1, 1, 12, 0, 0)
    end_date = datetime(2023, 1, 2, 12, 0, 0)

    # Mock the Github instance
    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = [
        Mock(oid="abc123", committed_date=start_date),
        Mock(oid="def456", committed_date=end_date),
    ]
    mock_github_instance.search_pull_requests.return_value = [mock_pr1, mock_pr2]

    result = get_pull_requests_between_commits(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="def456",
        github=mock_github_instance,
    )

    assert "Pull Requests between commits abc123 and def456" in result
    assert "test-owner/test-repo" in result
    assert "[test-owner/test-repo#123] Test PR 1" in result
    assert "[test-owner/test-repo#124] Test PR 2" in result


def test_get_pull_requests_between_commits_error_handling(mocker):
    """Test that errors in commit fetching are handled gracefully."""
    # Mock the Github instance to raise an error
    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = Exception("Test error")

    result = get_pull_requests_between_commits(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="def456",
        github=mock_github_instance,
    )

    # When commit fetching fails, the function now returns a more specific error message
    assert "Error occurred while fetching pull requests between commits" in result
    assert "Error getting start commit abc123 from test-owner/test-repo: Test error" in result


def test_get_pull_requests_between_commits_main_error_handling(mocker):
    """Test that errors in GitHub operations are handled gracefully."""
    # Mock the Github instance to raise an exception on any operation
    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = Exception("GitHub connection error")

    result = get_pull_requests_between_commits(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="def456",
        github=mock_github_instance,
    )

    assert "Error occurred while fetching pull requests between commits" in result
    assert "GitHub connection error" in result


def test_get_pull_requests_between_commits_end_commit_error(mocker):
    """Test that errors in fetching the end commit are handled gracefully."""
    start_date = datetime(2023, 1, 1, 12, 0, 0)

    # Mock the Github instance - first call succeeds, second fails
    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = [
        Mock(oid="abc123", committed_date=start_date),  # Start commit succeeds
        Exception("End commit not found"),  # End commit fails
    ]

    result = get_pull_requests_between_commits(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="def456",
        github=mock_github_instance,
    )

    assert "Error occurred while fetching pull requests between commits" in result
    assert "Error getting end commit def456 from test-owner/test-repo: End commit not found" in result


def test_get_pull_requests_between_commits_same_commits(mocker):
    """Test that when start and end commits are the same, no PRs are returned."""
    same_date = datetime(2023, 1, 1, 12, 0, 0)
    same_commit = Mock(oid="abc123", committed_date=same_date)

    # Mock the Github instance
    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = [same_commit, same_commit]

    result = get_pull_requests_between_commits(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="abc123",
        github=mock_github_instance,
    )

    assert "No pull requests found" in result
    assert "test-owner/test-repo" in result


def test_get_pull_requests_between_commits_with_merge_commit_filtering(mocker):
    """Test that PRs with merge commits matching the start commit are filtered out."""
    # Mock pull request objects - one should be filtered out
    mock_pr1 = Mock()
    mock_pr1.url = "https://github.com/test-owner/test-repo/pull/123"
    mock_pr1.uri = "test-owner/test-repo#123"
    mock_pr1.title = "Test PR 1"
    mock_pr1.merge_commit = Mock(oid="abc123")  # This should be filtered out

    mock_pr2 = Mock()
    mock_pr2.url = "https://github.com/test-owner/test-repo/pull/124"
    mock_pr2.uri = "test-owner/test-repo#124"
    mock_pr2.title = "Test PR 2"
    mock_pr2.merge_commit = Mock(oid="xyz789")  # This should remain

    # Create datetime objects for commit dates
    start_date = datetime(2023, 1, 1, 12, 0, 0)
    end_date = datetime(2023, 1, 2, 12, 0, 0)

    # Mock the Github instance
    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = [
        Mock(oid="abc123", committed_date=start_date),
        Mock(oid="def456", committed_date=end_date),
    ]
    mock_github_instance.search_pull_requests.return_value = [mock_pr1, mock_pr2]

    result = get_pull_requests_between_commits(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="def456",
        github=mock_github_instance,
    )

    # Verify the search was called with correct date range
    expected_search_query = "repo:test-owner/test-repo base:main merged:2022-12-31T23:59:50..2023-01-02T12:00:10"
    mock_github_instance.search_pull_requests.assert_called_once()
    call_args = mock_github_instance.search_pull_requests.call_args[0]
    assert "repo:test-owner/test-repo" in call_args[0]
    assert "base:main" in call_args[0]
    assert "merged:" in call_args[0]

    # Only PR 2 should be in the result (PR 1 filtered out due to matching merge commit)
    assert "Pull Requests between commits abc123 and def456" in result
    assert "[test-owner/test-repo#124] Test PR 2" in result
    assert "[test-owner/test-repo#123] Test PR 1" not in result


def test_search_pull_requests_between_dates_with_exclusion(mocker):
    """Test the internal search_pull_requests_between_dates function with commit exclusion."""
    from ai_tools_github.pull_requests_between_commits import search_pull_requests_between_dates

    # Mock pull request objects
    mock_pr1 = Mock()
    mock_pr1.merge_commit = Mock(oid="exclude_this")

    mock_pr2 = Mock()
    mock_pr2.merge_commit = Mock(oid="keep_this")

    mock_github_instance = Mock()
    mock_github_instance.search_pull_requests.return_value = [mock_pr1, mock_pr2]

    result = search_pull_requests_between_dates(
        github=mock_github_instance,
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_date_str="2023-01-01T00:00:00",
        end_date_str="2023-01-02T00:00:00",
        exclude_commit_oid="exclude_this",
    )

    # Only the second PR should be returned
    assert len(result) == 1
    assert result[0] == mock_pr2

    # Verify the search was called correctly
    expected_query = "repo:test-owner/test-repo base:main merged:2023-01-01T00:00:00..2023-01-02T00:00:00"
    mock_github_instance.search_pull_requests.assert_called_once_with(
        expected_query, querydata=mocker.ANY, instance_class=mocker.ANY
    )


def test_search_pull_requests_between_dates_no_exclusion(mocker):
    """Test the internal search_pull_requests_between_dates function without commit exclusion."""
    from ai_tools_github.pull_requests_between_commits import search_pull_requests_between_dates

    # Mock pull request objects
    mock_pr1 = Mock()
    mock_pr2 = Mock()

    mock_github_instance = Mock()
    mock_github_instance.search_pull_requests.return_value = [mock_pr1, mock_pr2]

    result = search_pull_requests_between_dates(
        github=mock_github_instance,
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_date_str="2023-01-01T00:00:00",
        end_date_str="2023-01-02T00:00:00",
        exclude_commit_oid=None,
    )

    # Both PRs should be returned
    assert len(result) == 2
    assert result[0] == mock_pr1
    assert result[1] == mock_pr2
