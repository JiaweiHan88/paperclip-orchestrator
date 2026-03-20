"""Tests for JIRA pull requests functionality."""

import unittest
from unittest.mock import Mock

from ai_tools_jira.pull_requests import JiraPullRequestsInput, get_jira_pull_requests


class TestJiraPullRequestsInput(unittest.TestCase):
    """Test the JiraPullRequestsInput pydantic model."""

    def test_valid_issue_key(self):
        """Test that valid issue keys are accepted."""
        valid_keys = ["IPNDEV-23605", "SWH-456", "MCP-789", "PROJECT-123"]
        for key in valid_keys:
            with self.subTest(issue_key=key):
                input_model = JiraPullRequestsInput(issue_key=key)
                self.assertEqual(input_model.issue_key, key)

    def test_empty_issue_key_allowed_in_model(self):
        """Test that empty strings are allowed in the model (validation happens in function)."""
        input_model = JiraPullRequestsInput(issue_key="")
        self.assertEqual(input_model.issue_key, "")


class TestGetJiraPullRequests(unittest.TestCase):
    """Test the get_jira_pull_requests function."""

    def test_empty_issue_key_raises_error(self):
        """Test that empty issue key raises ValueError."""
        mock_jira = Mock()
        with self.assertRaises(ValueError) as context:
            get_jira_pull_requests("", mock_jira)
        self.assertIn("Issue key cannot be empty", str(context.exception))

        with self.assertRaises(ValueError) as context:
            get_jira_pull_requests("   ", mock_jira)
        self.assertIn("Issue key cannot be empty", str(context.exception))

    def test_successful_response_with_items(self):
        """Test successful response with pull requests in 'items' field."""
        # Create mock jira instance with session and issue data
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the issue retrieval for text extraction
        mock_issue = Mock()
        mock_issue.fields.description = None
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        mock_jira.issue.return_value = mock_issue

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pullRequests": {
                "items": [
                    {"title": "Test PR 1", "url": "https://github.com/test/repo/pull/1", "state": "open"},
                    {"title": "Test PR 2", "url": "https://github.com/test/repo/pull/2", "state": "merged"},
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        result = get_jira_pull_requests("TEST-123", mock_jira)

        self.assertIn("Pull Requests for TEST-123", result)
        self.assertIn("## Linked Pull Requests", result)
        self.assertIn("Test PR 1", result)
        self.assertIn("Test PR 2", result)
        self.assertIn("https://github.com/test/repo/pull/1", result)
        self.assertIn("https://github.com/test/repo/pull/2", result)

    def test_successful_response_with_pull_requests(self):
        """Test successful response with pull requests in 'pullRequests' field."""
        # Create mock jira instance with session and issue data
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the issue retrieval for text extraction
        mock_issue = Mock()
        mock_issue.fields.description = None
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        mock_jira.issue.return_value = mock_issue

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pullRequests": {
                "items": [{"title": "Test PR 1", "url": "https://bitbucket.org/test/repo/pull/1", "state": "merged"}]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        result = get_jira_pull_requests("TEST-123", mock_jira)

        self.assertIn("Pull Requests for TEST-123", result)
        self.assertIn("## Linked Pull Requests", result)
        self.assertIn("Test PR 1", result)
        self.assertIn("https://bitbucket.org/test/repo/pull/1", result)

    def test_404_response_no_pull_requests(self):
        """Test 404 response indicating no pull requests found."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_session.get.return_value = mock_response

        # Expect the function to raise an exception on 404
        with self.assertRaises(Exception):
            get_jira_pull_requests("TEST-123", mock_jira)

    def test_empty_pull_requests_list(self):
        """Test response with empty pull requests list."""
        # Create mock jira instance with session and issue data
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the issue retrieval for text extraction
        mock_issue = Mock()
        mock_issue.fields.description = None
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        mock_jira.issue.return_value = mock_issue

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        result = get_jira_pull_requests("TEST-123", mock_jira)

        self.assertIn("Pull Requests for TEST-123", result)
        self.assertIn("## Linked Pull Requests", result)
        # Empty list should result in no items being listed in linked section
        lines = result.split("\n")
        linked_section_start = next(i for i, line in enumerate(lines) if "## Linked Pull Requests" in line)
        mentioned_section_start = next(
            i for i, line in enumerate(lines) if "## Pull Requests Mentioned in Text" in line
        )
        linked_lines = lines[linked_section_start:mentioned_section_start]
        self.assertEqual(len([line for line in linked_lines if line.startswith("- ")]), 0)

    def test_pull_request_without_url(self):
        """Test pull request data without URL (should raise KeyError)."""
        # Create mock jira instance with session
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pullRequests": {
                # Missing 'url' field
                "items": [{"title": "Test PR without URL", "state": "open"}]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # The function should fail if required fields are missing
        with self.assertRaises(KeyError):
            get_jira_pull_requests("TEST-123", mock_jira)

    def test_request_headers_and_url(self):
        """Test that request is made with correct headers and URL."""
        # Create mock jira instance with session and issue data
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the issue retrieval for text extraction
        mock_issue = Mock()
        mock_issue.fields.description = None
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        mock_jira.issue.return_value = mock_issue

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        get_jira_pull_requests("TEST-123", mock_jira)

        expected_url = "https://jira.cc.bmwgroup.net/rest/gitplugin/1.0/issuegitdetails/issue/TEST-123/pullRequest"
        mock_session.get.assert_called_once_with(expected_url)

    def test_pr_in_description_mentioned_section(self):
        """Test extracting PR URLs from issue description appears in mentioned section."""
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the API response (no linked PRs)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # Mock the issue retrieval for text extraction
        mock_issue = Mock()
        mock_issue.fields.description = "Fix implemented in https://github.com/owner/repo/pull/123"
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        mock_jira.issue.return_value = mock_issue

        result = get_jira_pull_requests("TEST-123", mock_jira)

        self.assertIn("Pull Requests for TEST-123", result)
        self.assertIn("## Pull Requests Mentioned in Text", result)
        self.assertIn("https://github.com/owner/repo/pull/123", result)

    def test_multiple_pr_urls_from_different_sources(self):
        """Test extracting PRs from both description and comments."""
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the API response (no linked PRs)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # Mock the issue with description and comments
        mock_issue = Mock()
        mock_issue.fields.description = "See https://github.com/owner/repo/pull/100"

        mock_comment1 = Mock()
        mock_comment1.body = "Related to https://gitlab.com/owner/repo/-/merge_requests/200"
        mock_comment2 = Mock()
        mock_comment2.body = "Also check https://bitbucket.org/owner/repo/pull-requests/300"

        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = [mock_comment1, mock_comment2]
        mock_jira.issue.return_value = mock_issue

        result = get_jira_pull_requests("TEST-123", mock_jira)

        self.assertIn("https://github.com/owner/repo/pull/100", result)
        self.assertIn("https://gitlab.com/owner/repo/-/merge_requests/200", result)
        self.assertIn("https://bitbucket.org/owner/repo/pull-requests/300", result)

    def test_azure_devops_pr_url(self):
        """Test extracting Azure DevOps PR URLs."""
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the API response (no linked PRs)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # Mock the issue
        mock_issue = Mock()
        mock_issue.fields.description = "Fix: https://dev.azure.com/org/project/_git/repo/pullrequest/456"
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        mock_jira.issue.return_value = mock_issue

        result = get_jira_pull_requests("TEST-123", mock_jira)

        self.assertIn("https://dev.azure.com/org/project/_git/repo/pullrequest/456", result)

    def test_no_pr_urls_found_in_text(self):
        """Test handling when no PR URLs are found in text."""
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the API response (no linked PRs)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # Mock the issue
        mock_issue = Mock()
        mock_issue.fields.description = "This is a regular issue description without any PR links."
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        mock_jira.issue.return_value = mock_issue

        result = get_jira_pull_requests("TEST-123", mock_jira)

        self.assertIn("Pull Requests for TEST-123", result)
        self.assertIn("## Pull Requests Mentioned in Text", result)
        self.assertIn("No pull request URLs found in text", result)

    def test_duplicate_urls_deduplicated_in_mentioned(self):
        """Test that duplicate URLs are deduplicated in mentioned section."""
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the API response (no linked PRs)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # Mock the issue
        mock_issue = Mock()
        mock_issue.fields.description = "PR: https://github.com/owner/repo/pull/123"

        mock_comment1 = Mock()
        mock_comment1.body = "See https://github.com/owner/repo/pull/123 again"
        mock_comment2 = Mock()
        mock_comment2.body = "Still https://github.com/owner/repo/pull/123"

        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = [mock_comment1, mock_comment2]
        mock_jira.issue.return_value = mock_issue

        result = get_jira_pull_requests("TEST-123", mock_jira)

        # Count occurrences of the URL in the result
        url_count = result.count("https://github.com/owner/repo/pull/123")
        self.assertEqual(url_count, 1, "URL should appear only once in the result")

    def test_null_description(self):
        """Test handling when issue description is None."""
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the API response (no linked PRs)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # Mock the issue
        mock_issue = Mock()
        mock_issue.fields.description = None
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        mock_jira.issue.return_value = mock_issue

        result = get_jira_pull_requests("TEST-123", mock_jira)

        self.assertIn("## Pull Requests Mentioned in Text", result)
        self.assertIn("No pull request URLs found in text", result)

    def test_null_comment_body(self):
        """Test handling when comment body is None."""
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the API response (no linked PRs)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # Mock the issue
        mock_issue = Mock()
        mock_issue.fields.description = "https://github.com/owner/repo/pull/100"

        mock_comment = Mock()
        mock_comment.body = None

        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = [mock_comment]
        mock_jira.issue.return_value = mock_issue

        result = get_jira_pull_requests("TEST-123", mock_jira)

        self.assertIn("https://github.com/owner/repo/pull/100", result)

    def test_custom_github_enterprise_url(self):
        """Test extracting custom GitHub Enterprise PR URLs."""
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the API response (no linked PRs)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # Mock the issue
        mock_issue = Mock()
        mock_issue.fields.description = "Fix: https://cc-github.bmwgroup.net/swh/ddad_platform/pull/68369"
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        mock_jira.issue.return_value = mock_issue

        result = get_jira_pull_requests("TEST-123", mock_jira)

        self.assertIn("https://cc-github.bmwgroup.net/swh/ddad_platform/pull/68369", result)

    def test_sorted_output_in_mentioned(self):
        """Test that PR URLs are sorted in the mentioned section."""
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the API response (no linked PRs)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pullRequests": {"items": []}}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # Mock the issue
        mock_issue = Mock()
        mock_issue.fields.description = """
        https://github.com/z/repo/pull/300
        https://github.com/a/repo/pull/100
        https://github.com/m/repo/pull/200
        """
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        mock_jira.issue.return_value = mock_issue

        result = get_jira_pull_requests("TEST-123", mock_jira)

        lines = result.split("\n")
        # Find the mentioned section
        mentioned_section_start = next(
            i for i, line in enumerate(lines) if "## Pull Requests Mentioned in Text" in line
        )
        pr_lines = [line for line in lines[mentioned_section_start:] if line.startswith("- https://")]

        # Check that URLs are in sorted order
        urls = [line.replace("- ", "") for line in pr_lines]
        self.assertEqual(urls, sorted(urls), "URLs should be sorted")

    def test_mentioned_pr_already_linked_filtered_out(self):
        """Test that PRs mentioned in text that are already linked are filtered out."""
        mock_jira = Mock()
        mock_session = Mock()
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://jira.cc.bmwgroup.net"}

        # Mock the API response (has linked PR)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pullRequests": {
                "items": [{"title": "Test PR", "url": "https://github.com/owner/repo/pull/123", "state": "merged"}]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # Mock the issue (same PR mentioned in description)
        mock_issue = Mock()
        mock_issue.fields.description = "See https://github.com/owner/repo/pull/123"
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        mock_jira.issue.return_value = mock_issue

        result = get_jira_pull_requests("TEST-123", mock_jira)

        # The PR should appear in Linked section
        self.assertIn("## Linked Pull Requests", result)
        self.assertIn("Test PR", result)

        # Count occurrences - should only appear once (in linked section)
        url_count = result.count("https://github.com/owner/repo/pull/123")
        self.assertEqual(url_count, 1, "URL should appear only once (in linked section, not mentioned)")


if __name__ == "__main__":
    unittest.main()
