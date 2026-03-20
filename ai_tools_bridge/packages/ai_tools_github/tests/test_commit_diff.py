"""Tests for the commit_diff module."""

import json
from unittest.mock import Mock

import pytest

from ai_tools_github.commit_diff import (
    CommitDiffInput,
    get_commit_diff,
    should_include_file,
)


class TestCommitDiffInput:
    """Test the CommitDiffInput model."""

    def test_valid_input(self):
        """Test valid input parameters."""
        input_data = CommitDiffInput(
            owner="owner",
            repo="repo",
            commit_sha="abc123",
        )
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.commit_sha == "abc123"
        assert input_data.file_scope is None

    def test_with_file_scope(self):
        """Test input with file scope filtering."""
        input_data = CommitDiffInput(owner="owner", repo="repo", commit_sha="abc123", file_scope=[".py", ".js"])
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.commit_sha == "abc123"
        assert input_data.file_scope == [".py", ".js"]


class TestShouldIncludeFile:
    """Test the should_include_file function."""

    def test_no_file_scope(self):
        """Test that all files are included when no file_scope is provided."""
        assert should_include_file("file.py", None) is True
        assert should_include_file("file.js", None) is True
        assert should_include_file("README.md", None) is True

    def test_extension_match(self):
        """Test file extension matching."""
        file_scope = [".py", ".js"]
        assert should_include_file("script.py", file_scope) is True
        assert should_include_file("app.js", file_scope) is True
        assert should_include_file("README.md", file_scope) is False

    def test_pattern_match(self):
        """Test pattern matching."""
        file_scope = ["test", "src"]
        assert should_include_file("test_file.py", file_scope) is True
        assert should_include_file("src/main.py", file_scope) is True
        assert should_include_file("docs/readme.md", file_scope) is False

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        file_scope = [".PY", ".JS"]
        assert should_include_file("script.py", file_scope) is True
        assert should_include_file("APP.JS", file_scope) is True


class TestGetCommitDiff:
    """Test the get_commit_diff function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_github = Mock()

    def test_get_commit_diff_success(self):
        """Test successful diff retrieval."""
        # Mock the GitHub API response
        commit_data = {
            "files": [
                {
                    "filename": "file1.py",
                    "status": "modified",
                    "patch": "@@ -1,3 +1,3 @@\n line1\n-old line\n+new line\n line3",
                },
                {"filename": "file2.js", "status": "added", "patch": "@@ -0,0 +1,2 @@\n+line1\n+line2"},
            ]
        }
        self.mock_github.v3_get.return_value = json.dumps(commit_data)

        result = get_commit_diff("owner", "repo", "abc123", self.mock_github)

        expected = """--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,3 @@
 line1
-old line
+new line
 line3

--- a/file2.js
+++ b/file2.js
@@ -0,0 +1,2 @@
+line1
+line2"""
        assert result == expected

    def test_get_commit_diff_with_file_scope_filtering(self):
        """Test diff retrieval with file scope filtering."""
        # Mock response with Python and lock files
        commit_data = {
            "files": [
                {"filename": "script.py", "status": "modified", "patch": "@@ -1,1 +1,1 @@\n-old\n+new"},
                {"filename": "package-lock.json", "status": "modified", "patch": "@@ -1,1 +1,1 @@\n-old\n+new"},
            ]
        }
        self.mock_github.v3_get.return_value = json.dumps(commit_data)

        result = get_commit_diff("owner", "repo", "abc123", self.mock_github, file_scope=[".py"])

        # Should only include Python files
        assert "script.py" in result
        assert "package-lock.json" not in result

    def test_get_commit_diff_no_patch_content(self):
        """Test diff when patch content is not available."""
        commit_data = {
            "files": [
                {
                    "filename": "binary_file.png",
                    "status": "added",
                    # No patch content for binary files
                }
            ]
        }
        self.mock_github.v3_get.return_value = json.dumps(commit_data)

        result = get_commit_diff("owner", "repo", "abc123", self.mock_github)

        expected = "--- a/binary_file.png\n+++ b/binary_file.png\nFile added: binary_file.png"
        assert result == expected

    def test_get_commit_diff_no_relevant_files(self):
        """Test diff when no files match the scope."""
        commit_data = {
            "files": [{"filename": "package-lock.json", "status": "modified", "patch": "@@ -1,1 +1,1 @@\n-old\n+new"}]
        }
        self.mock_github.v3_get.return_value = json.dumps(commit_data)

        result = get_commit_diff("owner", "repo", "abc123", self.mock_github, file_scope=[".py"])

        assert result == "No relevant changes found (file scope: ['.py'])"

    def test_get_commit_diff_no_files(self):
        """Test diff when commit has no files."""
        commit_data = {}
        self.mock_github.v3_get.return_value = json.dumps(commit_data)

        result = get_commit_diff("owner", "repo", "abc123", self.mock_github)

        assert result == "No diff available"

    def test_get_commit_diff_api_error(self):
        """Test diff when API call fails."""
        self.mock_github.v3_get.side_effect = Exception("API Error")

        result = get_commit_diff("owner", "repo", "abc123", self.mock_github)

        assert result == "Diff unavailable"
