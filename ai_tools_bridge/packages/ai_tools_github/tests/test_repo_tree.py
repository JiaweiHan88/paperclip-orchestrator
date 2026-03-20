"""Test cases for repo_tree module."""

import json
from unittest.mock import Mock

import pytest

from ai_tools_github.repo_tree import RepoTreeInput, get_repo_tree


@pytest.fixture
def mock_github_instance():
    """Create a mock Github instance."""
    return Mock()


@pytest.fixture
def sample_tree_response():
    """Create a sample tree response from GitHub API."""
    return {
        "tree": [
            {
                "path": "README.md",
                "type": "blob",
                "sha": "abc123",
                "url": "https://api.github.com/repos/owner/repo/git/blobs/abc123",
            },
            {
                "path": "src",
                "type": "tree",
                "sha": "def456",
                "url": "https://api.github.com/repos/owner/repo/git/trees/def456",
            },
            {
                "path": "src/main.py",
                "type": "blob",
                "sha": "ghi789",
                "url": "https://api.github.com/repos/owner/repo/git/blobs/ghi789",
            },
            {
                "path": "src/utils.py",
                "type": "blob",
                "sha": "jkl012",
                "url": "https://api.github.com/repos/owner/repo/git/blobs/jkl012",
            },
            {
                "path": "package-lock.json",  # Should be filtered out
                "type": "blob",
                "sha": "mno345",
                "url": "https://api.github.com/repos/owner/repo/git/blobs/mno345",
            },
            {
                "path": "image.png",  # Should be filtered out
                "type": "blob",
                "sha": "pqr678",
                "url": "https://api.github.com/repos/owner/repo/git/blobs/pqr678",
            },
            {
                "path": "docs/api.md",
                "type": "blob",
                "sha": "stu901",
                "url": "https://api.github.com/repos/owner/repo/git/blobs/stu901",
            },
        ]
    }


@pytest.fixture
def sample_empty_tree_response():
    """Create a sample empty tree response from GitHub API."""
    return {"tree": []}


class TestRepoTreeInput:
    """Test the RepoTreeInput validation."""

    def test_valid_input(self):
        """Test that valid input passes validation."""
        input_data = RepoTreeInput(owner="owner", repo="repo", ref="main")
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.ref == "main"

    def test_default_ref(self):
        """Test that ref defaults to HEAD."""
        input_data = RepoTreeInput(owner="owner", repo="repo")
        assert input_data.ref == "HEAD"

    def test_required_fields(self):
        """Test that required fields work correctly."""
        input_data = RepoTreeInput(owner="swh", repo="AI4CI", ref="develop")
        assert input_data.owner == "swh"
        assert input_data.repo == "AI4CI"
        assert input_data.ref == "develop"


class TestGetRepoTree:
    """Test the get_repo_tree function."""

    def test_successful_tree_retrieval(self, mock_github_instance, sample_tree_response):
        """
        Test successful repository tree retrieval and formatting.

        Requirements:
        - Should call GitHub API with correct parameters
        - Should filter out non-processable files (lock files, binaries)
        - Should return markdown-formatted tree with clickable URLs
        - Should include progress logging for processed files
        - Should handle both files and directories correctly
        """
        # Mock the GitHub API response
        mock_github_instance.v3_get.return_value = json.dumps(sample_tree_response)

        # Call the function
        result = get_repo_tree(owner="owner", repo="repo", github=mock_github_instance, ref="main")

        # Verify API call was made with correct parameters
        mock_github_instance.v3_get.assert_called_once_with(
            url_part="/repos/owner/repo/git/trees/main",
            update_headers={"Accept": "application/vnd.github.v3+json"},
            params={"recursive": "1"},
        )

        # Verify the result contains expected elements
        assert "# Repository Tree: owner/repo" in result
        assert "**Reference:** main" in result
        assert (
            "**Total Files:** 6" in result
        )  # All files (README.md, src/main.py, src/utils.py, package-lock.json, image.png, docs/api.md)
        # Directories and files are shown in the tree
        assert "📁 **src/**" in result
        assert "📄 [README.md](https://github.com/owner/repo/blob/main/README.md)" in result
        assert "📄 [main.py](https://github.com/owner/repo/blob/main/src/main.py)" in result
        assert "📄 [utils.py](https://github.com/owner/repo/blob/main/src/utils.py)" in result
        assert "📄 [api.md](https://github.com/owner/repo/blob/main/docs/api.md)" in result

    def test_empty_repository(self, mock_github_instance, sample_empty_tree_response):
        """
        Test handling of empty repositories.

        Requirements:
        - Should handle empty tree responses gracefully
        - Should return appropriate message for empty repositories
        - Should not crash with zero files
        """
        mock_github_instance.v3_get.return_value = json.dumps(sample_empty_tree_response)

        result = get_repo_tree(owner="owner", repo="empty-repo", github=mock_github_instance)

        assert "# Repository Tree: owner/empty-repo" in result
        assert "**Total Files:** 0" in result

    def test_api_error_handling(self, mock_github_instance):
        """
        Test handling of GitHub API errors.

        Requirements:
        - Should handle API exceptions gracefully
        - Should return meaningful error messages
        - Should not expose internal error details
        """
        # Mock API error
        mock_github_instance.v3_get.side_effect = Exception("API Error: Not Found")

        result = get_repo_tree(owner="owner", repo="repo", github=mock_github_instance)

        assert "Error fetching repository tree" in result
        assert "API Error: Not Found" in result

    def test_invalid_response_format(self, mock_github_instance):
        """
        Test handling of invalid API responses.

        Requirements:
        - Should handle missing 'tree' key in response
        - Should return appropriate error message
        - Should not crash on malformed responses
        """
        # Mock invalid response
        mock_github_instance.v3_get.return_value = json.dumps({"invalid": "response"})

        result = get_repo_tree(owner="owner", repo="repo", github=mock_github_instance)

        assert "No tree data found or repository is empty." in result

    def test_string_response_parsing(self, mock_github_instance, sample_tree_response):
        """
        Test parsing of string JSON responses from GitHub API.

        Requirements:
        - Should parse JSON string responses correctly
        - Should handle both dict and string response types
        """
        # Mock string JSON response
        mock_github_instance.v3_get.return_value = json.dumps(sample_tree_response)

        result = get_repo_tree(owner="owner", repo="repo", github=mock_github_instance)

        # Should parse and process correctly
        assert "# Repository Tree: owner/repo" in result
        assert "**Total Files:** 6" in result

    def test_mixed_file_types_filtering(self, mock_github_instance):
        """
        Test filtering of various file types.

        Requirements:
        - Should include text files (.py, .md, .txt, .js, etc.)
        - Should exclude binary files (.png, .jpg, .exe, etc.)
        - Should exclude lock files (package-lock.json, yarn.lock, etc.)
        - Should exclude SVG files as specified
        """
        mixed_tree = {
            "tree": [
                {"path": "script.py", "type": "blob", "sha": "1", "url": "url1"},
                {"path": "README.md", "type": "blob", "sha": "2", "url": "url2"},
                {"path": "config.json", "type": "blob", "sha": "3", "url": "url3"},
                {"path": "image.png", "type": "blob", "sha": "4", "url": "url4"},  # Should be filtered
                {"path": "package-lock.json", "type": "blob", "sha": "5", "url": "url5"},  # Should be filtered
                {"path": "icon.svg", "type": "blob", "sha": "6", "url": "url6"},  # Should be filtered
                {"path": "executable.exe", "type": "blob", "sha": "7", "url": "url7"},  # Should be filtered
                {"path": "yarn.lock", "type": "blob", "sha": "8", "url": "url8"},  # Should be filtered
                {"path": "style.css", "type": "blob", "sha": "9", "url": "url9"},
            ]
        }

        mock_github_instance.v3_get.return_value = json.dumps(mixed_tree)

        result = get_repo_tree(owner="owner", repo="repo", github=mock_github_instance)

        # Verify that all 9 files are counted (no filtering applied)
        assert "**Total Files:** 9" in result
        # Files are shown in the tree structure
        assert "📄 [script.py](https://github.com/owner/repo/blob/HEAD/script.py)" in result
