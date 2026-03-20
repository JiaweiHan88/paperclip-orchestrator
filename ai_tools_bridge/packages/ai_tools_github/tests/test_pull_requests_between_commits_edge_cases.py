"""Additional edge case tests for pull_requests_between_commits functionality."""

from datetime import datetime
from unittest.mock import Mock

from ai_tools_github.pull_requests_between_commits import (
    PullRequestsBetweenCommitsInput,
    get_pull_requests_between_commits,
    search_pull_requests_between_commits,
    search_pull_requests_between_dates,
)


def test_pull_requests_between_commits_input_edge_cases():
    """Test input validation with edge cases."""
    # Test with valid minimal input (empty strings are currently allowed by the model)
    input_data = PullRequestsBetweenCommitsInput(
        owner="",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="def456",
    )
    assert input_data.owner == ""
    assert input_data.repo == "test-repo"

    # Test with valid minimal input
    input_data = PullRequestsBetweenCommitsInput(
        owner="o",
        repo="r",
        branch="b",
        start_commit_hash="a",
        end_commit_hash="b",
    )
    assert input_data.owner == "o"
    assert input_data.repo == "r"


def test_search_pull_requests_between_commits_reverse_chronology(mocker):
    """Test when end commit is older than start commit."""
    # End commit is older than start commit
    start_date = datetime(2023, 1, 2, 12, 0, 0)  # Later
    end_date = datetime(2023, 1, 1, 12, 0, 0)  # Earlier

    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = [
        Mock(oid="abc123", committed_date=start_date),
        Mock(oid="def456", committed_date=end_date),
    ]
    mock_github_instance.search_pull_requests.return_value = []

    result = search_pull_requests_between_commits(
        github=mock_github_instance,
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="def456",
    )

    # Should still work and call search with reversed dates
    assert result == []
    mock_github_instance.search_pull_requests.assert_called_once()


def test_search_pull_requests_between_dates_empty_results():
    """Test _search_pull_requests_between_dates with no results."""
    mock_github_instance = Mock()
    mock_github_instance.search_pull_requests.return_value = []

    result = search_pull_requests_between_dates(
        github=mock_github_instance,
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_date_str="2023-01-01T00:00:00",
        end_date_str="2023-01-02T00:00:00",
    )

    assert result == []


def test_search_pull_requests_between_dates_all_filtered():
    """Test when all PRs are filtered out due to matching exclude_commit_oid."""
    # All PRs have the same merge commit that should be excluded
    mock_pr1 = Mock()
    mock_pr1.merge_commit = Mock(oid="exclude_me")

    mock_pr2 = Mock()
    mock_pr2.merge_commit = Mock(oid="exclude_me")

    mock_github_instance = Mock()
    mock_github_instance.search_pull_requests.return_value = [mock_pr1, mock_pr2]

    result = search_pull_requests_between_dates(
        github=mock_github_instance,
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_date_str="2023-01-01T00:00:00",
        end_date_str="2023-01-02T00:00:00",
        exclude_commit_oid="exclude_me",
    )

    assert result == []


def test_get_pull_requests_between_commits_special_characters_in_repo_name(mocker):
    """Test with repository names containing special characters."""
    start_date = datetime(2023, 1, 1, 12, 0, 0)
    end_date = datetime(2023, 1, 2, 12, 0, 0)

    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = [
        Mock(oid="abc123", committed_date=start_date),
        Mock(oid="def456", committed_date=end_date),
    ]
    mock_github_instance.search_pull_requests.return_value = []

    # Test with special characters in repo name
    result = get_pull_requests_between_commits(
        owner="my-org",
        repo="my-repo.with.dots",
        branch="feature/test-branch",
        start_commit_hash="abc123",
        end_commit_hash="def456",
        github=mock_github_instance,
    )

    assert "No pull requests found" in result
    assert "my-org/my-repo.with.dots" in result
    assert "feature/test-branch" in result


def test_get_pull_requests_between_commits_long_commit_hashes(mocker):
    """Test with full 40-character commit hashes."""
    start_date = datetime(2023, 1, 1, 12, 0, 0)
    end_date = datetime(2023, 1, 2, 12, 0, 0)

    long_start_hash = "1234567890abcdef1234567890abcdef12345678"
    long_end_hash = "abcdef1234567890abcdef1234567890abcdef12"

    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = [
        Mock(oid=long_start_hash, committed_date=start_date),
        Mock(oid=long_end_hash, committed_date=end_date),
    ]
    mock_github_instance.search_pull_requests.return_value = []

    result = get_pull_requests_between_commits(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash=long_start_hash,
        end_commit_hash=long_end_hash,
        github=mock_github_instance,
    )

    assert "No pull requests found" in result
    assert long_start_hash in result
    assert long_end_hash in result


def test_get_pull_requests_between_commits_many_prs(mocker):
    """Test with a large number of pull requests returned."""
    start_date = datetime(2023, 1, 1, 12, 0, 0)
    end_date = datetime(2023, 1, 2, 12, 0, 0)

    # Create many mock PRs
    mock_prs = []
    for i in range(50):
        mock_pr = Mock()
        mock_pr.url = f"https://github.com/test-owner/test-repo/pull/{i + 1}"
        mock_pr.uri = f"test-owner/test-repo#{i + 1}"
        mock_pr.title = f"Test PR {i + 1}"
        mock_prs.append(mock_pr)

    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = [
        Mock(oid="abc123", committed_date=start_date),
        Mock(oid="def456", committed_date=end_date),
    ]
    mock_github_instance.search_pull_requests.return_value = mock_prs

    result = get_pull_requests_between_commits(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="def456",
        github=mock_github_instance,
    )

    # Should list all PRs
    assert "Pull Requests between commits abc123 and def456" in result
    assert "Test PR 1" in result
    assert "Test PR 50" in result
    # Count the number of PR entries (each PR should appear once)
    pr_count = result.count("[test-owner/test-repo#")
    assert pr_count == 50


def test_get_pull_requests_between_commits_prs_with_special_titles(mocker):
    """Test with PRs that have special characters in titles."""
    start_date = datetime(2023, 1, 1, 12, 0, 0)
    end_date = datetime(2023, 1, 2, 12, 0, 0)

    # PRs with various special characters in titles
    mock_pr1 = Mock()
    mock_pr1.url = "https://github.com/test-owner/test-repo/pull/1"
    mock_pr1.uri = "test-owner/test-repo#1"
    mock_pr1.title = "Fix: [urgent] Resolve issue with ñ & special chars ⚠️"

    mock_pr2 = Mock()
    mock_pr2.url = "https://github.com/test-owner/test-repo/pull/2"
    mock_pr2.uri = "test-owner/test-repo#2"
    mock_pr2.title = "feat(scope): Add 中文 support with émojis 🚀"

    mock_pr3 = Mock()
    mock_pr3.url = "https://github.com/test-owner/test-repo/pull/3"
    mock_pr3.uri = "test-owner/test-repo#3"
    mock_pr3.title = 'Update README.md with "quoted" text & <html> tags'

    mock_github_instance = Mock()
    mock_github_instance.get_commit_for_expression.side_effect = [
        Mock(oid="abc123", committed_date=start_date),
        Mock(oid="def456", committed_date=end_date),
    ]
    mock_github_instance.search_pull_requests.return_value = [mock_pr1, mock_pr2, mock_pr3]

    result = get_pull_requests_between_commits(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        start_commit_hash="abc123",
        end_commit_hash="def456",
        github=mock_github_instance,
    )

    # All special characters should be preserved
    assert "Fix: [urgent] Resolve issue with ñ & special chars ⚠️" in result
    assert "feat(scope): Add 中文 support with émojis 🚀" in result
    assert 'Update README.md with "quoted" text & <html> tags' in result


def test_get_pull_requests_between_commits_github_instance_usage(mocker):
    """Test that the github instance parameter is correctly used."""
    start_date = datetime(2023, 1, 1, 12, 0, 0)
    end_date = datetime(2023, 1, 2, 12, 0, 0)

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

    # Verify the github instance methods were called
    assert mock_github_instance.get_commit_for_expression.call_count == 2
    assert mock_github_instance.search_pull_requests.call_count == 1
    assert "No pull requests found" in result
