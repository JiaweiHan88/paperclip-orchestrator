"""Test cases for file_content module."""

from unittest.mock import Mock

import pytest

from ai_tools_github.file_content import FileContentInput, get_file_content


@pytest.fixture
def mock_github_instance():
    """Create a mock Github instance."""
    return Mock()


class TestFileContentInput:
    """Test the FileContentInput validation."""

    def test_valid_input(self):
        """Test that valid input passes validation."""
        input_data = FileContentInput(
            owner="owner",
            repo="repo",
            file_path="src/main.py",
            ref="main",
            max_file_size=100000,
        )
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.file_path == "src/main.py"
        assert input_data.ref == "main"
        assert input_data.max_file_size == 100000

    def test_default_values(self):
        """Test that defaults are applied correctly."""
        input_data = FileContentInput(owner="owner", repo="repo", file_path="README.md")
        assert input_data.ref == "HEAD"
        assert input_data.max_file_size == 50000

    def test_required_fields(self):
        """Test that required fields work correctly."""
        input_data = FileContentInput(
            owner="swh",
            repo="AI4CI",
            file_path="docs/api.md",
            ref="develop",
        )
        assert input_data.owner == "swh"
        assert input_data.repo == "AI4CI"
        assert input_data.file_path == "docs/api.md"


class TestGetFileContent:
    """Test the get_file_content function."""

    def test_successful_file_retrieval(self, mock_github_instance):
        """
        Test successful file content retrieval.

        Requirements:
        - Should call Github client's get_file_content with correct parameters
        - Should return raw file content as string
        - Should handle UTF-8 encoding properly
        """
        # Mock the Github client get_file_content response
        expected_content = (
            "# Sample File\n\nThis is a sample Python file.\n\ndef hello_world():\n    print('Hello, World!')\n"
        )
        mock_github_instance.get_file_content.return_value = expected_content

        # Call the function
        result = get_file_content(
            owner="owner", repo="repo", file_path="src/sample.py", github=mock_github_instance, ref="main"
        )

        # Verify API call was made with correct parameters
        mock_github_instance.get_file_content.assert_called_once_with("owner", "repo", "main", "src/sample.py")

        # Verify the result
        assert result == expected_content

    def test_binary_file_rejection(self, mock_github_instance):
        """Test that binary files are processed (no filtering applied)."""
        # Mock successful file content retrieval
        mock_github_instance.get_file_content.return_value = "binary content"

        result = get_file_content(owner="owner", repo="repo", file_path="image.png", github=mock_github_instance)

        # Should make API call since no filtering is applied
        mock_github_instance.get_file_content.assert_called_once_with("owner", "repo", "HEAD", "image.png")
        assert result == "binary content"

    def test_lock_file_rejection(self, mock_github_instance):
        """
        Test that lock files are processed (no filtering applied).
        """
        # Mock successful file content retrieval
        mock_github_instance.get_file_content.return_value = "lock file content"

        test_cases = [
            "package-lock.json",
            "yarn.lock",
            "poetry.lock",
            "Gemfile.lock",
            "composer.lock",
        ]

        for lock_file in test_cases:
            result = get_file_content(owner="owner", repo="repo", file_path=lock_file, github=mock_github_instance)

            # Should process the file since no filtering is applied
            assert result == "lock file content"

    def test_file_size_limit_exceeded(self, mock_github_instance):
        """
        Test handling of files exceeding size limit.

        Requirements:
        - Should check file size after getting content
        - Should return appropriate error message with size information
        - Should respect custom max_file_size parameter
        """
        # Create large content (60000 characters)
        large_content = "x" * 60000
        mock_github_instance.get_file_content.return_value = large_content

        result = get_file_content(
            owner="owner", repo="repo", file_path="large.txt", github=mock_github_instance, max_file_size=50000
        )

        # Verify API call was made
        mock_github_instance.get_file_content.assert_called_once()

        # Verify error message contains size information
        assert "Error: File too large" in result
        assert "60000 characters" in result
        assert "limit: 50000" in result

    def test_file_not_found_error(self, mock_github_instance):
        """
        Test handling of file not found errors.

        Requirements:
        - Should handle 404 errors gracefully
        - Should return user-friendly error message
        - Should not expose internal API error details
        """
        # Mock 404 error
        mock_github_instance.get_file_content.side_effect = Exception("404: Not Found")

        result = get_file_content(owner="owner", repo="repo", file_path="nonexistent.txt", github=mock_github_instance)

        assert "Error: File 'nonexistent.txt' not found in repository" in result

    def test_access_denied_error(self, mock_github_instance):
        """
        Test handling of access denied errors.

        Requirements:
        - Should handle 403 Forbidden errors
        - Should return appropriate access denied message
        """
        # Mock 403 error
        mock_github_instance.get_file_content.side_effect = Exception("403 Forbidden")

        result = get_file_content(owner="owner", repo="repo", file_path="private.txt", github=mock_github_instance)

        assert "Error: Access denied to repository or file" in result

    def test_authentication_error(self, mock_github_instance):
        """
        Test handling of authentication errors.

        Requirements:
        - Should handle 401 Unauthorized errors
        - Should return appropriate authentication error message
        """
        # Mock 401 error
        mock_github_instance.get_file_content.side_effect = Exception("401 Unauthorized")

        result = get_file_content(owner="owner", repo="repo", file_path="file.txt", github=mock_github_instance)

        assert "Error: Authentication required" in result

    def test_generic_api_error(self, mock_github_instance):
        """
        Test handling of other API errors.

        Requirements:
        - Should handle unexpected API errors gracefully
        - Should include error message in response
        - Should not crash on unexpected errors
        """
        # Mock generic error
        mock_github_instance.get_file_content.side_effect = Exception("Service Unavailable")

        result = get_file_content(owner="owner", repo="repo", file_path="file.txt", github=mock_github_instance)

        assert "Error fetching file content: Service Unavailable" in result

    def test_custom_file_size_limit(self, mock_github_instance):
        """
        Test using custom file size limits.

        Requirements:
        - Should respect custom max_file_size parameter
        - Should process files within custom limit
        - Should reject files exceeding custom limit
        """
        # File should be accepted with high limit
        expected_content = (
            "# Sample File\n\nThis is a sample Python file.\n\ndef hello_world():\n    print('Hello, World!')\n"
        )
        mock_github_instance.get_file_content.return_value = expected_content

        result = get_file_content(
            owner="owner",
            repo="repo",
            file_path="src/sample.py",
            github=mock_github_instance,
            max_file_size=100000,
        )

        # Should return content since it's within limit
        assert result == expected_content
