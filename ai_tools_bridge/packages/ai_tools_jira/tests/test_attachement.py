"""Tests for Jira attachment functionality.

This module contains comprehensive tests for downloading Jira attachments,
including success cases, error handling, and edge cases.
"""

import unittest
from unittest.mock import Mock, mock_open, patch

import requests
from pydantic import ValidationError

from ai_tools_jira.attachment import JiraAttachmentDownloadInput, download_jira_attachment


class TestJiraAttachmentDownloadInput(unittest.TestCase):
    """Test cases for the JiraAttachmentDownloadInput Pydantic model.

    Tests validation of input parameters and model behavior.
    """

    def test_valid_input_with_required_fields_only(self):
        """Test that model accepts valid input with only required fields."""
        input_data = JiraAttachmentDownloadInput(attachment_id="12345", download_path="./downloads/file_name.jpg")
        self.assertEqual(input_data.attachment_id, "12345")
        self.assertEqual(input_data.download_path, "./downloads/file_name.jpg")

    def test_valid_input_with_all_fields(self):
        """Test that model accepts valid input with all fields provided."""
        input_data = JiraAttachmentDownloadInput(
            attachment_id="67890",
            download_path="/tmp/test/file.pdf",
        )
        self.assertEqual(input_data.attachment_id, "67890")
        self.assertEqual(input_data.download_path, "/tmp/test/file.pdf")

    def test_empty_attachment_id_raises_validation_error(self):
        """Test that empty attachment_id raises ValidationError."""
        with self.assertRaises(ValidationError):
            JiraAttachmentDownloadInput(attachment_id="")

    def test_missing_attachment_id_raises_validation_error(self):
        """Test that missing attachment_id raises ValidationError."""
        with self.assertRaises(ValidationError):
            JiraAttachmentDownloadInput(download_path="/tmp/test.pdf")


class TestDownloadJiraAttachment(unittest.TestCase):
    """Test cases for the download_jira_attachment function.

    Tests successful downloads, error conditions, and edge cases using mocks
    to avoid actual API calls and file system operations.
    """

    def setUp(self):
        """Set up test fixtures and common test data."""
        self.attachment_id = "12345"
        self.token = "test_token"
        self.mock_attachment_info = {
            "filename": "test_document.pdf",
            "size": 1024,
            "mimeType": "application/pdf",
            "content": "https://jira.cc.bmwgroup.net/secure/attachment/12345/test_document.pdf",
        }
        self.mock_file_content = b"mock file content"

    def test_successful_download_with_default_filename(self):
        """Test successful attachment download using the original filename."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the metadata response
        mock_metadata_response = Mock()
        mock_metadata_response.raise_for_status.return_value = None
        mock_metadata_response.json.return_value = self.mock_attachment_info

        # Mock the content response
        mock_content_response = Mock()
        mock_content_response.raise_for_status.return_value = None
        mock_content_response.content = self.mock_file_content

        # Configure session.get to return different responses for metadata and content
        mock_session.get.side_effect = [mock_metadata_response, mock_content_response]

        # Use patch for file operations
        with patch("builtins.open", mock_open()) as mock_file:
            # Call the function
            result = download_jira_attachment(
                attachment_id=self.attachment_id, jira_instance=mock_jira, download_path="/tmp/test_document.pdf"
            )

            # Verify the result
            expected_result = (
                f"Successfully downloaded attachment {self.attachment_id} to /tmp/test_document.pdf. "
                f"The file has the size 1024 and a mime type application/pdf."
            )
            self.assertEqual(result, expected_result)

            # Verify API calls
            self.assertEqual(mock_session.get.call_count, 2)

            # Verify metadata API call
            metadata_call = mock_session.get.call_args_list[0]
            expected_url = f"https://jira.cc.bmwgroup.net/rest/api/2/attachment/{self.attachment_id}"
            self.assertEqual(metadata_call[0][0], expected_url)

            # Verify content download call
            content_call = mock_session.get.call_args_list[1]
            self.assertEqual(content_call[0][0], self.mock_attachment_info["content"])

            # Verify file was written
            mock_file().write.assert_called_once_with(self.mock_file_content)

    def test_successful_download_with_custom_filename(self):
        """Test successful attachment download with a custom filename."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock responses
        mock_metadata_response = Mock()
        mock_metadata_response.raise_for_status.return_value = None
        mock_metadata_response.json.return_value = self.mock_attachment_info

        mock_content_response = Mock()
        mock_content_response.raise_for_status.return_value = None
        mock_content_response.content = self.mock_file_content

        mock_session.get.side_effect = [mock_metadata_response, mock_content_response]

        # Use patch for file operations
        with patch("builtins.open", mock_open()):
            # Call the function with custom filename
            result = download_jira_attachment(
                attachment_id=self.attachment_id,
                jira_instance=mock_jira,
                download_path="/tmp/custom_name.pdf",
            )

            # Verify the result includes original metadata but custom filename is used
            self.assertIn("Successfully downloaded attachment", result)
            self.assertIn("size 1024", result)
            self.assertIn("mime type application/pdf", result)

    def test_metadata_request_failure(self):
        """Test that HTTP errors during metadata retrieval are properly raised."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock a failed metadata request
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_session.get.return_value = mock_response

        # Verify the exception is raised
        with self.assertRaises(requests.HTTPError):
            download_jira_attachment(
                attachment_id=self.attachment_id, jira_instance=mock_jira, download_path="/tmp/test.pdf"
            )

    def test_missing_download_url_in_metadata(self):
        """Test that missing download URL in metadata raises ValueError."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock metadata response without content URL
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "filename": "test.pdf",
            "size": 1024,
            "mimeType": "application/pdf",
            # Missing 'content' field
        }
        mock_session.get.return_value = mock_response

        # Verify ValueError is raised
        with self.assertRaises(ValueError) as context:
            download_jira_attachment(
                attachment_id=self.attachment_id, jira_instance=mock_jira, download_path="/tmp/test.pdf"
            )

        self.assertEqual(str(context.exception), "No download URL found in attachment metadata")

    def test_empty_download_url_in_metadata(self):
        """Test that empty download URL in metadata raises ValueError."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock metadata response with empty content URL
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "filename": "test.pdf",
            "size": 1024,
            "mimeType": "application/pdf",
            "content": "",  # Empty content URL
        }
        mock_session.get.return_value = mock_response

        # Verify ValueError is raised
        with self.assertRaises(ValueError) as context:
            download_jira_attachment(
                attachment_id=self.attachment_id, jira_instance=mock_jira, download_path="/tmp/test.pdf"
            )

        self.assertEqual(str(context.exception), "No download URL found in attachment metadata")

    def test_content_download_failure(self):
        """Test that HTTP errors during content download are properly raised."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock successful metadata response
        mock_metadata_response = Mock()
        mock_metadata_response.raise_for_status.return_value = None
        mock_metadata_response.json.return_value = self.mock_attachment_info

        # Mock failed content response
        mock_content_response = Mock()
        mock_content_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")

        mock_session.get.side_effect = [mock_metadata_response, mock_content_response]

        # Verify the exception is raised
        with self.assertRaises(requests.HTTPError):
            download_jira_attachment(
                attachment_id=self.attachment_id, jira_instance=mock_jira, download_path="/tmp/test.pdf"
            )

    def test_fallback_filename_when_not_in_metadata(self):
        """Test that fallback filename is used when filename is missing from metadata."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock metadata without filename
        attachment_info_no_filename = {
            "size": 512,
            "mimeType": "text/plain",
            "content": "https://jira.cc.bmwgroup.net/secure/attachment/12345/content",
        }

        mock_metadata_response = Mock()
        mock_metadata_response.raise_for_status.return_value = None
        mock_metadata_response.json.return_value = attachment_info_no_filename

        mock_content_response = Mock()
        mock_content_response.raise_for_status.return_value = None
        mock_content_response.content = b"test content"

        mock_session.get.side_effect = [mock_metadata_response, mock_content_response]

        # Use patch for file operations
        with patch("builtins.open", mock_open()):
            # Call the function
            result = download_jira_attachment(
                attachment_id=self.attachment_id, jira_instance=mock_jira, download_path="/tmp/attachment_12345"
            )

            # Verify fallback filename behavior and result
            self.assertIn("Successfully downloaded attachment", result)
            self.assertIn("size 512", result)
            self.assertIn("mime type text/plain", result)

    def test_directory_creation(self):
        """Test that parent directories are created when they don't exist."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock successful responses
        mock_metadata_response = Mock()
        mock_metadata_response.raise_for_status.return_value = None
        mock_metadata_response.json.return_value = self.mock_attachment_info

        mock_content_response = Mock()
        mock_content_response.raise_for_status.return_value = None
        mock_content_response.content = self.mock_file_content

        mock_session.get.side_effect = [mock_metadata_response, mock_content_response]

        # Use patch for file operations and Path
        with patch("builtins.open", mock_open()), patch("ai_tools_jira.attachment.Path") as mock_path_class:
            # Mock Path operations to verify directory creation
            mock_path_instance = Mock()
            mock_parent_dir = Mock()
            mock_path_instance.parent = mock_parent_dir
            mock_path_class.return_value = mock_path_instance

            download_jira_attachment(
                attachment_id=self.attachment_id, jira_instance=mock_jira, download_path="/deep/nested/path/file.pdf"
            )

            # Verify that mkdir was called with correct parameters
            mock_parent_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_request_headers_are_correct(self):
        """Test that correct authorization headers are sent in both requests."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock responses
        mock_metadata_response = Mock()
        mock_metadata_response.raise_for_status.return_value = None
        mock_metadata_response.json.return_value = self.mock_attachment_info

        mock_content_response = Mock()
        mock_content_response.raise_for_status.return_value = None
        mock_content_response.content = self.mock_file_content

        mock_session.get.side_effect = [mock_metadata_response, mock_content_response]

        # Use patch for file operations
        with patch("builtins.open", mock_open()):
            # Call the function
            download_jira_attachment(
                attachment_id=self.attachment_id, jira_instance=mock_jira, download_path="/tmp/test.pdf"
            )

            # Verify both requests were made
            self.assertEqual(mock_session.get.call_count, 2)

    def test_no_timeout_values_are_set(self):
        """Test that no timeout values are set for requests (using session defaults)."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock responses
        mock_metadata_response = Mock()
        mock_metadata_response.raise_for_status.return_value = None
        mock_metadata_response.json.return_value = self.mock_attachment_info

        mock_content_response = Mock()
        mock_content_response.raise_for_status.return_value = None
        mock_content_response.content = self.mock_file_content

        mock_session.get.side_effect = [mock_metadata_response, mock_content_response]

        # Use patch for file operations
        with patch("builtins.open", mock_open()):
            # Call the function
            download_jira_attachment(
                attachment_id=self.attachment_id, jira_instance=mock_jira, download_path="/tmp/test.pdf"
            )

            # Verify no timeout values are passed (using session defaults)
            metadata_call = mock_session.get.call_args_list[0]
            self.assertNotIn("timeout", metadata_call[1])

            content_call = mock_session.get.call_args_list[1]
            self.assertNotIn("timeout", content_call[1])


if __name__ == "__main__":
    unittest.main()
