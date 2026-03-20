"""Test cases for repo_folder_files_path module."""

import json
from unittest.mock import Mock

import pytest

from ai_tools_github.repo_folder_files_path import (
    RepoFolderFilesPathInput,
    get_repo_folder_files_path,
)


@pytest.fixture
def mock_github_instance():
    """Create a mock Github instance."""
    return Mock()


@pytest.fixture
def sample_tree_response():
    """Create a sample GitHub tree response as JSON string."""
    return json.dumps(
        {
            "tree": [
                {"path": "zuul.d/pipelines/check.yaml", "type": "blob"},
                {"path": "zuul.d/pipelines/post.yaml", "type": "blob"},
                {"path": "zuul.d/pipelines/release.yaml", "type": "blob"},
                {"path": "zuul.d/projects/adp-projects.yaml", "type": "blob"},
                {"path": "zuul.d/projects/ncar-projects.yaml", "type": "blob"},
                {"path": "README.md", "type": "blob"},
                {"path": "zuul.d", "type": "tree"},
                {"path": "zuul.d/pipelines", "type": "tree"},
                {"path": "zuul.d/projects", "type": "tree"},
            ]
        }
    )


class TestRepoFolderFilesPathInput:
    """Tests for RepoFolderFilesPathInput schema."""

    def test_input_schema_defaults(self):
        """Test schema with default values."""
        input_data = RepoFolderFilesPathInput(
            owner="swh",
            repo="zuul-trusted-ddad",
        )
        assert input_data.owner == "swh"
        assert input_data.repo == "zuul-trusted-ddad"
        assert input_data.ref == "HEAD"
        assert input_data.folder_path == ""

    def test_input_schema_with_all_fields(self):
        """Test schema with all fields specified."""
        input_data = RepoFolderFilesPathInput(
            owner="microsoft",
            repo="vscode",
            ref="main",
            folder_path="src/",
        )
        assert input_data.owner == "microsoft"
        assert input_data.repo == "vscode"
        assert input_data.ref == "main"
        assert input_data.folder_path == "src/"


class TestGetRepoFolderFilesPath:
    """Tests for get_repo_folder_files_path function."""

    def test_get_files_in_folder(self, mock_github_instance, sample_tree_response):
        """Test retrieving files from a specific folder."""
        mock_github_instance.v3_get.return_value = sample_tree_response

        result = get_repo_folder_files_path(
            owner="swh",
            repo="zuul-trusted-ddad",
            github=mock_github_instance,
            ref="HEAD",
            folder_path="zuul.d/pipelines/",
        )

        assert "# Files in swh/zuul-trusted-ddad/zuul.d/pipelines/" in result
        assert "**Reference:** HEAD" in result
        assert "**Total Files:** 3" in result
        assert "## Files" in result
        assert "- zuul.d/pipelines/check.yaml" in result
        assert "- zuul.d/pipelines/post.yaml" in result
        assert "- zuul.d/pipelines/release.yaml" in result
        assert "zuul.d/projects/adp-projects.yaml" not in result  # Different folder

    def test_get_files_with_normalized_folder_path(self, mock_github_instance, sample_tree_response):
        """Test that folder path is normalized to include trailing slash."""
        mock_github_instance.v3_get.return_value = sample_tree_response

        # Folder path without trailing slash
        result = get_repo_folder_files_path(
            owner="swh",
            repo="zuul-trusted-ddad",
            github=mock_github_instance,
            folder_path="zuul.d/pipelines",
        )

        assert "**Total Files:** 3" in result
        assert "- zuul.d/pipelines/check.yaml" in result

    def test_get_files_empty_folder(self, mock_github_instance):
        """Test behavior when folder contains no files."""
        empty_response = json.dumps(
            {
                "tree": [
                    {"path": "zuul.d/empty_folder", "type": "tree"},
                    {"path": "README.md", "type": "blob"},
                ]
            }
        )
        mock_github_instance.v3_get.return_value = empty_response

        result = get_repo_folder_files_path(
            owner="swh",
            repo="zuul-trusted-ddad",
            github=mock_github_instance,
            folder_path="zuul.d/empty_folder/",
        )

        assert "**Total Files:** 0" in result
        assert "No files found in this folder." in result

    def test_get_files_default_folder_path(self, mock_github_instance, sample_tree_response):
        """Test with empty folder_path returns all files with full paths."""
        mock_github_instance.v3_get.return_value = sample_tree_response

        result = get_repo_folder_files_path(
            owner="swh",
            repo="zuul-trusted-ddad",
            github=mock_github_instance,
            folder_path="",
        )

        # Should include all blobs (files) with full paths
        assert "**Total Files:** 6" in result
        assert "- README.md" in result
        assert "- zuul.d/pipelines/check.yaml" in result
        assert "- zuul.d/projects/adp-projects.yaml" in result

    def test_get_files_with_github_links(self, mock_github_instance, sample_tree_response):
        """Test that returned files are listed without GitHub links."""
        mock_github_instance.v3_get.return_value = sample_tree_response

        result = get_repo_folder_files_path(
            owner="swh",
            repo="zuul-trusted-ddad",
            github=mock_github_instance,
            ref="main",
            folder_path="zuul.d/pipelines/",
        )

        # Should have full file paths without markdown links
        assert "- zuul.d/pipelines/check.yaml" in result
        assert "- zuul.d/pipelines/post.yaml" in result
        # Should not have GitHub URLs
        assert "https://github.com" not in result

    def test_get_files_handles_string_response(self, mock_github_instance, sample_tree_response):
        """Test that string JSON responses are parsed correctly."""
        mock_github_instance.v3_get.return_value = sample_tree_response

        result = get_repo_folder_files_path(
            owner="swh",
            repo="zuul-trusted-ddad",
            github=mock_github_instance,
            folder_path="zuul.d/pipelines/",
        )

        assert "**Total Files:** 3" in result
        assert "- zuul.d/pipelines/check.yaml" in result

    def test_get_files_handles_missing_tree(self, mock_github_instance):
        """Test error handling when response has no tree data."""
        mock_github_instance.v3_get.return_value = json.dumps({"message": "Not Found"})

        result = get_repo_folder_files_path(
            owner="swh",
            repo="nonexistent-repo",
            github=mock_github_instance,
            folder_path="zuul.d/pipelines/",
        )

        assert "No tree data found or repository is empty." in result

    def test_get_files_handles_api_exception(self, mock_github_instance):
        """Test error handling when API call raises exception."""
        mock_github_instance.v3_get.side_effect = Exception("API Error")

        result = get_repo_folder_files_path(
            owner="swh",
            repo="zuul-trusted-ddad",
            github=mock_github_instance,
            folder_path="zuul.d/pipelines/",
        )

        assert "Error fetching folder files:" in result
        assert "API Error" in result

    def test_files_sorted_in_output(self, mock_github_instance):
        """Test that files are sorted alphabetically in output."""
        tree_response = json.dumps(
            {
                "tree": [
                    {"path": "zuul.d/z-file.yaml", "type": "blob"},
                    {"path": "zuul.d/a-file.yaml", "type": "blob"},
                    {"path": "zuul.d/m-file.yaml", "type": "blob"},
                ]
            }
        )
        mock_github_instance.v3_get.return_value = tree_response

        result = get_repo_folder_files_path(
            owner="swh",
            repo="zuul-trusted-ddad",
            github=mock_github_instance,
            folder_path="zuul.d/",
        )

        # Check that files appear in sorted order in the output
        a_index = result.find("- zuul.d/a-file.yaml")
        m_index = result.find("- zuul.d/m-file.yaml")
        z_index = result.find("- zuul.d/z-file.yaml")

        assert a_index < m_index < z_index

    def test_get_files_correct_api_call(self, mock_github_instance, sample_tree_response):
        """Test that the correct API endpoint is called."""
        mock_github_instance.v3_get.return_value = sample_tree_response

        get_repo_folder_files_path(
            owner="swh",
            repo="zuul-trusted-ddad",
            github=mock_github_instance,
            ref="main",
            folder_path="zuul.d/pipelines/",
        )

        mock_github_instance.v3_get.assert_called_once()
        call_args = mock_github_instance.v3_get.call_args
        assert "url_part" in call_args.kwargs
        assert "/repos/swh/zuul-trusted-ddad/git/trees/main" in call_args.kwargs["url_part"]
        assert call_args.kwargs["params"]["recursive"] == "1"
