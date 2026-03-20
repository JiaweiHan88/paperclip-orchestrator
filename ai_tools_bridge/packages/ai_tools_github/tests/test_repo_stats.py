"""Test cases for repo_stats module."""

from unittest.mock import Mock

import pytest

from ai_tools_github.repo_stats import RepoStatsInput, get_repo_stats, is_bot_author


@pytest.fixture
def mock_github_instance():
    """Create a mock Github instance."""
    return Mock()


@pytest.fixture
def sample_stats_response():
    """Create a sample repository stats response from GraphQL."""
    return {
        "repository": {
            "name": "test-repo",
            "url": "https://github.com/owner/test-repo",
            "description": "A test repository for demonstration",
            "createdAt": "2025-01-01T10:00:00Z",
            "updatedAt": "2025-11-18T20:18:55Z",
            "stargazerCount": 42,
            "forkCount": 10,
            "watchers": {"totalCount": 15},
            "primaryLanguage": {"name": "Python"},
            "languages": {"nodes": [{"name": "Python"}, {"name": "JavaScript"}, {"name": "HTML"}]},
            "repositoryTopics": {
                "nodes": [{"topic": {"name": "test"}}, {"topic": {"name": "demo"}}, {"topic": {"name": "python"}}]
            },
            "defaultBranchRef": {
                "name": "main",
                "target": {
                    "history": {
                        "totalCount": 100,
                        "nodes": [
                            {
                                "author": {
                                    "name": "Test User",
                                    "email": "test@example.com",
                                    "user": {"login": "testuser"},
                                }
                            },
                            {
                                "author": {
                                    "name": "Another User",
                                    "email": "another@example.com",
                                    "user": {"login": "anotheruser"},
                                }
                            },
                            {
                                "author": {
                                    "name": "GitHub Actions",
                                    "email": "actions@github.com",
                                    "user": {"login": "github-actions[bot]"},
                                }
                            },
                        ],
                    }
                },
            },
            "diskUsage": 2048,  # 2048 KB = 2 MB
            "isPrivate": False,
            "isArchived": False,
            "isFork": False,
            "licenseInfo": {"name": "MIT License", "spdxId": "MIT", "url": "https://opensource.org/licenses/MIT"},
            "openIssues": {"totalCount": 5},
            "closedIssues": {"totalCount": 15},
            "openPullRequests": {"totalCount": 3},
            "closedPullRequests": {"totalCount": 8},
            "mergedPullRequests": {"totalCount": 12},
            "releases": {"nodes": [{"name": "v1.0.0", "createdAt": "2025-11-01T10:00:00Z", "tagName": "v1.0.0"}]},
        }
    }


class TestRepoStatsInput:
    """Test the RepoStatsInput validation."""

    def test_valid_input(self):
        """Test that valid input passes validation."""
        input_data = RepoStatsInput(owner="owner", repo="repo")
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"

    def test_examples(self):
        """Test with example values."""
        input_data = RepoStatsInput(owner="octocat", repo="Hello-World")
        assert input_data.owner == "octocat"
        assert input_data.repo == "Hello-World"


class TestUtilityFunctions:
    """Test utility functions."""

    def test_is_bot_author(self):
        """Test bot author detection."""
        # Test bot patterns
        assert is_bot_author("github-actions[bot]") is True
        assert is_bot_author("dependabot[bot]") is True
        assert is_bot_author("renovate[bot]") is True
        assert is_bot_author("codecov-bot") is True
        assert is_bot_author("snyk-bot") is True
        assert is_bot_author("zuul[bot]") is True

        # Test case insensitive
        assert is_bot_author("GITHUB-ACTIONS[BOT]") is True
        assert is_bot_author("Bot-User") is True

        # Test human users
        assert is_bot_author("testuser") is False
        assert is_bot_author("john.doe") is False
        assert is_bot_author("contributor123") is False

        # Test edge cases
        assert is_bot_author("") is False
        assert is_bot_author("robot") is True  # contains "bot"


class TestGetRepoStats:
    """Test the get_repo_stats function."""

    def test_successful_stats_retrieval(self, mock_github_instance, sample_stats_response):
        """
        Test successful repository statistics retrieval.

        Requirements:
        - Should call GraphQL API with correct repository query
        - Should return comprehensive markdown-formatted statistics
        - Should include all repository metadata and metrics
        - Should format numbers with thousands separators
        - Should handle contributor analysis correctly
        """
        # Mock the GraphQL response
        mock_github_instance.query.return_value = sample_stats_response

        # Call the function
        result = get_repo_stats(owner="owner", repo="test-repo", github=mock_github_instance)

        # Verify GraphQL query was made
        mock_github_instance.query.assert_called_once()

        # Check that query contains correct repository parameters
        call_args = mock_github_instance.query.call_args[0][0]
        assert 'repository(owner: "owner", name: "test-repo")' in call_args

        # Verify basic repository information
        assert "# Repository Statistics: test-repo" in result
        assert "**URL:** https://github.com/owner/test-repo" in result
        assert "**Description:** A test repository for demonstration" in result
        assert "**Created:** 2025-01-01 10:00:00" in result
        assert "**Last Updated:** 2025-11-18 20:18:55" in result
        assert "**Status:** Public" in result

        # Verify statistics
        assert "**Stars:** 42" in result
        assert "**Forks:** 10" in result
        assert "**Watchers:** 15" in result

        # Verify issues and pull requests
        assert "**Issues:** 5 open, 15 closed (20 total)" in result
        assert "**Pull Requests:** 3 open, 12 merged, 8 closed (23 total)" in result

        # Verify commit information
        assert "**Total Commits:** 100" in result
        assert "**Default Branch:** main" in result

        # Verify language information
        assert "**Primary Language:** Python" in result
        assert "**Languages:** Python, JavaScript, HTML" in result

        # Verify topics
        assert "**Topics:** test, demo, python" in result

        # Verify license
        assert "**License:** MIT License (MIT)" in result

        # Verify repository size
        assert "**Repository Size:** 2.00 MB" in result

        # Verify release information
        assert "**Latest Release:** v1.0.0 (v1.0.0) - 2025-11-01 10:00:00" in result

        # Verify contributors section
        assert "## Contributors" in result
        assert "**Total Contributors:** 2" in result  # Excluding bots
        assert "**Top Contributors (by commits):**" in result

    def test_private_repository(self, mock_github_instance, sample_stats_response):
        """Test handling of private repositories."""
        # Modify response to be private
        sample_stats_response["repository"]["isPrivate"] = True
        mock_github_instance.query.return_value = sample_stats_response

        result = get_repo_stats(owner="owner", repo="private-repo", github=mock_github_instance)

        assert "**Status:** Private" in result

    def test_archived_repository(self, mock_github_instance, sample_stats_response):
        """Test handling of archived repositories."""
        # Modify response to be archived
        sample_stats_response["repository"]["isArchived"] = True
        mock_github_instance.query.return_value = sample_stats_response

        result = get_repo_stats(owner="owner", repo="archived-repo", github=mock_github_instance)

        assert "**Status:** Public, Archived" in result

    def test_fork_repository(self, mock_github_instance, sample_stats_response):
        """Test handling of forked repositories."""
        # Modify response to be a fork
        sample_stats_response["repository"]["isFork"] = True
        mock_github_instance.query.return_value = sample_stats_response

        result = get_repo_stats(owner="owner", repo="forked-repo", github=mock_github_instance)

        assert "**Status:** Public, Fork" in result

    def test_repository_without_description(self, mock_github_instance, sample_stats_response):
        """Test handling of repositories without description."""
        # Remove description
        sample_stats_response["repository"]["description"] = None
        mock_github_instance.query.return_value = sample_stats_response

        result = get_repo_stats(owner="owner", repo="no-desc-repo", github=mock_github_instance)

        assert "**Description:** No description" in result

    def test_repository_without_license(self, mock_github_instance, sample_stats_response):
        """Test handling of repositories without license."""
        # Remove license info
        sample_stats_response["repository"]["licenseInfo"] = None
        mock_github_instance.query.return_value = sample_stats_response

        result = get_repo_stats(owner="owner", repo="no-license-repo", github=mock_github_instance)

        # Should not contain license information
        assert "License:" not in result

    def test_repository_without_releases(self, mock_github_instance, sample_stats_response):
        """Test handling of repositories without releases."""
        # Remove releases
        sample_stats_response["repository"]["releases"]["nodes"] = []
        mock_github_instance.query.return_value = sample_stats_response

        result = get_repo_stats(owner="owner", repo="no-releases-repo", github=mock_github_instance)

        # Should not contain release information
        assert "Latest Release:" not in result

    def test_large_repository_size(self, mock_github_instance, sample_stats_response):
        """Test handling of large repository sizes."""
        # Set large size (2GB)
        sample_stats_response["repository"]["diskUsage"] = 2048 * 1024  # 2GB in KB
        mock_github_instance.query.return_value = sample_stats_response

        result = get_repo_stats(owner="owner", repo="large-repo", github=mock_github_instance)

        assert "**Repository Size:** 2.00 GB" in result

    def test_api_error_handling(self, mock_github_instance):
        """Test handling of GraphQL API errors."""
        error_response = {"errors": [{"message": "Repository not found"}]}
        mock_github_instance.query.return_value = error_response

        result = get_repo_stats(owner="owner", repo="nonexistent", github=mock_github_instance)

        assert "Error fetching repository data" in result

    def test_repository_not_found(self, mock_github_instance):
        """Test handling when repository is not found."""
        not_found_response = {"repository": None}
        mock_github_instance.query.return_value = not_found_response

        result = get_repo_stats(owner="owner", repo="notfound", github=mock_github_instance)

        assert "Repository not found or access denied." in result

    def test_generic_exception_handling(self, mock_github_instance):
        """Test handling of unexpected exceptions."""
        mock_github_instance.query.side_effect = Exception("Network error")

        result = get_repo_stats(owner="owner", repo="test-repo", github=mock_github_instance)

        assert "Error: Network error" in result

    def test_empty_commit_history(self, mock_github_instance, sample_stats_response):
        """Test handling of repositories with no commit history."""
        # Remove commit history
        sample_stats_response["repository"]["defaultBranchRef"] = None
        mock_github_instance.query.return_value = sample_stats_response

        result = get_repo_stats(owner="owner", repo="empty-repo", github=mock_github_instance)

        # Should still work without crashing
        assert "# Repository Statistics: test-repo" in result  # Uses name from response, not parameters
        assert "No contributors data available" in result
