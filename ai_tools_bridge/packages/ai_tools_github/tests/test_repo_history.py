"""Tests for the repo_history module."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from ai_tools_github.repo_history import (
    RepoHistoryInput,
    format_diff_stats,
    get_repo_history,
    parse_timestamp,
    should_include_commit,
)


class TestRepoHistoryInput:
    """Test the RepoHistoryInput model."""

    def test_valid_input(self):
        """Test valid input parameters."""
        input_data = RepoHistoryInput(
            owner="owner",
            repo="repo",
            limit=25,
        )
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.limit == 25

    def test_default_values(self):
        """Test default values."""
        input_data = RepoHistoryInput(owner="owner", repo="repo")
        assert input_data.limit == 50
        assert input_data.from_timestamp is None
        assert input_data.to_timestamp is None
        assert input_data.file_scope is None

    def test_all_fields(self):
        """Test all fields including optional timestamps."""
        input_data = RepoHistoryInput(
            owner="owner",
            repo="repo",
            limit=25,
            from_timestamp="2025-11-18T20:18:55Z",
            to_timestamp="2025-11-20T20:18:55Z",
            file_scope=[".py", ".js"],
        )
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.limit == 25
        assert input_data.from_timestamp == "2025-11-18T20:18:55Z"
        assert input_data.to_timestamp == "2025-11-20T20:18:55Z"
        assert input_data.file_scope == [".py", ".js"]

    def test_limit_validation(self):
        """Test limit parameter validation."""
        input_data = RepoHistoryInput(owner="owner", repo="repo", limit=100)
        assert input_data.limit == 100


class TestUtilityFunctions:
    """Test utility functions."""

    def test_parse_timestamp(self):
        """Test timestamp parsing."""
        timestamp_with_z = "2025-11-18T20:18:55Z"
        dt = parse_timestamp(timestamp_with_z)
        assert isinstance(dt, datetime)
        assert dt.year == 2025
        assert dt.month == 11
        assert dt.day == 18
        assert dt.hour == 20
        assert dt.minute == 18
        assert dt.second == 55

    def test_parse_timestamp_without_z(self):
        """Test timestamp parsing without Z suffix."""
        timestamp_iso = "2025-11-18T20:18:55+00:00"
        dt = parse_timestamp(timestamp_iso)
        assert isinstance(dt, datetime)
        assert dt.year == 2025

    def test_should_include_commit(self):
        """Test commit filtering by timestamp."""
        # Test without filter
        assert should_include_commit("2025-11-18T20:18:55Z", None) is True

        # Test with from_timestamp filter - commit after threshold
        assert should_include_commit("2025-11-18T20:18:55Z", "2025-11-18T00:00:00Z") is True

        # Test with from_timestamp filter - commit before threshold
        assert should_include_commit("2025-11-17T20:18:55Z", "2025-11-18T00:00:00Z") is False

        # Test with from_timestamp filter - commit exactly at threshold
        assert should_include_commit("2025-11-18T00:00:00Z", "2025-11-18T00:00:00Z") is True

    def test_format_diff_stats(self):
        """Test diff statistics formatting."""
        # Test normal case
        result = format_diff_stats(10, 5)
        assert result == "+10 -5 (15 total changes)"

        # Test no changes
        result = format_diff_stats(0, 0)
        assert result == "No changes"

        # Test only additions
        result = format_diff_stats(10, 0)
        assert result == "+10 -0 (10 total changes)"

        # Test only deletions
        result = format_diff_stats(0, 5)
        assert result == "+0 -5 (5 total changes)"

        # Test large numbers
        result = format_diff_stats(1000, 500)
        assert result == "+1000 -500 (1500 total changes)"


class TestGetRepoHistory:
    """Test the get_repo_history function."""

    @pytest.fixture
    def mock_github_instance(self):
        """Create a mock Github instance."""
        return Mock()

    @pytest.fixture
    def sample_history_response(self):
        """Create a sample history response from GraphQL."""
        return {
            "repository": {
                "name": "test-repo",
                "url": "https://github.com/owner/test-repo",
                "defaultBranchRef": {
                    "name": "main",
                    "target": {
                        "history": {
                            "totalCount": 2,
                            "nodes": [
                                {
                                    "oid": "abc123def456",
                                    "message": "Initial commit",
                                    "committedDate": "2025-11-18T20:18:55Z",
                                    "author": {
                                        "name": "Test User",
                                        "email": "test@example.com",
                                        "user": {"login": "testuser"},
                                    },
                                    "additions": 10,
                                    "deletions": 0,
                                    "associatedPullRequests": {"nodes": []},
                                },
                                {
                                    "oid": "def456ghi789",
                                    "message": "Fix bug in authentication",
                                    "committedDate": "2025-11-18T19:00:00Z",
                                    "author": {
                                        "name": "Another User",
                                        "email": "another@example.com",
                                        "user": {"login": "anotheruser"},
                                    },
                                    "additions": 5,
                                    "deletions": 3,
                                    "associatedPullRequests": {
                                        "nodes": [
                                            {
                                                "number": 42,
                                                "title": "Fix authentication bug",
                                                "url": "https://github.com/owner/test-repo/pull/42",
                                            }
                                        ]
                                    },
                                },
                            ],
                        }
                    },
                },
            }
        }

    def test_successful_history_retrieval(self, mock_github_instance, sample_history_response):
        """Test successful repository history retrieval."""
        # Mock the GraphQL response
        mock_github_instance.query.return_value = sample_history_response

        # Call the function
        result = get_repo_history(owner="owner", repo="test-repo", github=mock_github_instance, limit=50)

        # Verify GraphQL query was made
        mock_github_instance.query.assert_called_once()

        # Check that query contains correct repository parameters
        call_args = mock_github_instance.query.call_args[0][0]
        assert 'repository(owner: "owner", name: "test-repo")' in call_args

        # Verify the result contains expected sections
        assert "# Repository History: test-repo" in result
        assert "**URL:** https://github.com/owner/test-repo" in result
        assert "## Timeline (2 total commits)" in result
        assert "**Default Branch:** main" in result

        # Check commit information
        assert "abc123de" in result  # Short SHA
        assert "Initial commit" in result
        assert "Test User (@testuser)" in result
        assert "+10 -0 (10 total changes)" in result

        assert "def456gh" in result  # Short SHA
        assert "Fix bug in authentication" in result
        assert "Another User (@anotheruser)" in result
        assert "+5 -3 (8 total changes)" in result
        assert "(PR #42: Fix authentication bug)" in result

    def test_empty_repository(self, mock_github_instance):
        """Test handling of empty repositories."""
        empty_response = {
            "repository": {
                "name": "empty-repo",
                "url": "https://github.com/owner/empty-repo",
                "defaultBranchRef": None,
            }
        }
        mock_github_instance.query.return_value = empty_response

        result = get_repo_history(owner="owner", repo="empty-repo", github=mock_github_instance)

        assert "# Repository History: empty-repo" in result
        assert "No commit history available" in result

    def test_api_error_handling(self, mock_github_instance):
        """Test handling of GraphQL API errors."""
        error_response = {"errors": [{"message": "Repository not found"}]}
        mock_github_instance.query.return_value = error_response

        result = get_repo_history(owner="owner", repo="nonexistent", github=mock_github_instance)

        assert "Error fetching repository data" in result

    def test_repository_not_found(self, mock_github_instance):
        """Test handling when repository is not found."""
        not_found_response = {"repository": None}
        mock_github_instance.query.return_value = not_found_response

        result = get_repo_history(owner="owner", repo="notfound", github=mock_github_instance)

        assert "Repository not found or access denied." in result

    def test_with_timestamp_filters(self, mock_github_instance, sample_history_response):
        """Test timestamp filtering functionality."""
        mock_github_instance.query.return_value = sample_history_response

        result = get_repo_history(
            owner="owner",
            repo="test-repo",
            github=mock_github_instance,
            from_timestamp="2025-11-18T00:00:00Z",
            to_timestamp="2025-11-20T00:00:00Z",
        )

        # Verify filter information is displayed
        assert "**Date Filter:** from 2025-11-18T00:00:00Z to 2025-11-20T00:00:00Z" in result

    def test_with_file_scope(self, mock_github_instance, sample_history_response):
        """Test file scope filtering."""
        mock_github_instance.query.return_value = sample_history_response

        result = get_repo_history(
            owner="owner", repo="test-repo", github=mock_github_instance, file_scope=[".py", ".js"]
        )

        # Verify file scope information is displayed
        assert "**File Scope:** .py, .js" in result

    def test_generic_exception_handling(self, mock_github_instance):
        """Test handling of unexpected exceptions."""
        mock_github_instance.query.side_effect = Exception("Network error")

        result = get_repo_history(owner="owner", repo="test-repo", github=mock_github_instance)

        assert "Error: Network error" in result
