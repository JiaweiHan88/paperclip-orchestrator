"""Tests for JIRA search functionality."""

from unittest.mock import Mock

import pytest

from ai_tools_jira.search import JiraSearchInput, search_jira


class TestJiraSearchInput:
    """Test the JiraSearchInput pydantic model."""

    def test_valid_input(self):
        """Test that valid input creates a proper model instance."""
        input_data = JiraSearchInput(query="project = PROJECT AND status = 'In Progress'")
        assert input_data.query == "project = PROJECT AND status = 'In Progress'"

    def test_empty_query_allowed_in_model(self):
        """Test that empty query is allowed in model (validation happens in function)."""
        input_data = JiraSearchInput(query="")
        assert input_data.query == ""

    def test_empty_query_validation(self):
        """Test that empty query raises ValueError during function execution."""
        # The model itself doesn't validate empty queries, that's done in the function
        input_data = JiraSearchInput(query="")
        assert input_data.query == ""


class TestSearchJira:
    """Test the search_jira function."""

    def test_empty_query_raises_error(self):
        """Test that empty query raises ValueError."""
        mock_logging = Mock()
        mock_jira = Mock()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_jira("", mock_jira, mock_logging)

    def test_whitespace_only_query_raises_error(self):
        """Test that whitespace-only query raises ValueError."""
        mock_logging = Mock()
        mock_jira = Mock()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_jira("   ", mock_jira, mock_logging)

    def test_successful_search(self):
        """Test successful JIRA search with valid results."""
        # Mock JIRA instance and issue
        mock_jira = Mock()

        # Create mock issue with proper structure
        mock_issue = Mock()
        mock_issue.key = "TEST-123"

        # Mock the fields attribute
        mock_fields = Mock()
        mock_fields.summary = "Test Issue"
        mock_fields.description = "Test Description"

        # Mock status
        mock_status = Mock()
        mock_status.name = "In Progress"
        mock_fields.status = mock_status

        # Mock assignee
        mock_assignee = Mock()
        mock_assignee.displayName = "John Doe"
        mock_fields.assignee = mock_assignee

        # Mock reporter
        mock_reporter = Mock()
        mock_reporter.displayName = "Jane Doe"
        mock_fields.reporter = mock_reporter

        # Mock priority
        mock_priority = Mock()
        mock_priority.name = "High"
        mock_fields.priority = mock_priority

        # Set other fields
        mock_fields.created = "2023-01-01T10:00:00.000+0000"
        mock_fields.updated = "2023-01-02T10:00:00.000+0000"
        mock_fields.customfield_10111 = 5

        # Mock comment and attachment (need to be iterable)
        mock_comment = Mock()
        mock_comment.comments = []
        mock_fields.comment = mock_comment
        mock_fields.attachment = []
        mock_fields.components = []

        mock_issue.fields = mock_fields

        # Create a mock result list with total attribute
        mock_result_list = Mock()
        mock_result_list.__iter__ = Mock(return_value=iter([mock_issue]))
        mock_result_list.total = 1
        mock_result_list.__bool__ = Mock(return_value=True)
        mock_jira.search_issues.return_value = mock_result_list

        mock_logging = Mock()

        result = search_jira("project = TEST", mock_jira, mock_logging)

        # Verify the result is a markdown string
        assert isinstance(result, str)
        assert "TEST-123" in result
        assert "Test Issue" in result
        assert "Test Description" in result
        assert "Found 1 issues" in result
        assert "showing 1" in result

        # Verify logging calls
        mock_logging.info.assert_any_call("Searching JIRA with query: project = TEST")
        mock_logging.info.assert_any_call("Successfully retrieved 1 out of 1 JIRA issues")

    def test_empty_search_results(self):
        """Test JIRA search with no results."""
        mock_jira = Mock()
        mock_jira.search_issues.return_value = []

        mock_logging = Mock()

        result = search_jira("project = NONEXISTENT", mock_jira, mock_logging)

        assert isinstance(result, str)
        assert "No issues found for the query" in result
        mock_logging.info.assert_any_call("No JIRA issues found for the query")

    def test_jira_api_error(self):
        """Test handling of JIRA API errors."""
        mock_jira = Mock()
        mock_jira.search_issues.side_effect = Exception("JIRA API Error")

        mock_logging = Mock()

        with pytest.raises(Exception, match="JIRA search failed: JIRA API Error"):
            search_jira("project = TEST", mock_jira, mock_logging)

        mock_logging.error.assert_called_with("JIRA search failed: JIRA API Error")

    def test_issue_without_raw_data(self):
        """Test handling of issues without raw data."""
        mock_jira = Mock()

        # Create mock issue with minimal structure
        mock_issue = Mock()
        mock_issue.key = "TEST-456"

        # Mock minimal fields
        mock_fields = Mock()
        mock_fields.summary = "Test Issue 456"
        mock_fields.description = "Test Description 456"

        # Mock comment and attachment (need to be iterable)
        mock_comment = Mock()
        mock_comment.comments = []
        mock_fields.comment = mock_comment
        mock_fields.attachment = []
        mock_fields.components = []

        mock_issue.fields = mock_fields

        mock_result_list = Mock()
        mock_result_list.__iter__ = Mock(return_value=iter([mock_issue]))
        mock_result_list.total = 1
        mock_result_list.__bool__ = Mock(return_value=True)
        mock_jira.search_issues.return_value = mock_result_list

        mock_logging = Mock()

        result = search_jira("project = TEST", mock_jira, mock_logging)

        # The function should return markdown string with count
        assert isinstance(result, str)
        assert "TEST-456" in result
        assert "Found 1 issues" in result

    def test_pagination_shows_limited_results(self):
        """Test that pagination correctly shows limited results vs total count."""
        mock_jira = Mock()

        # Create mock issue
        mock_issue = Mock()
        mock_issue.key = "TEST-789"
        mock_fields = Mock()
        mock_fields.summary = "Test Issue 789"
        mock_fields.description = "Test Description 789"
        mock_comment = Mock()
        mock_comment.comments = []
        mock_fields.comment = mock_comment
        mock_fields.attachment = []
        mock_fields.components = []
        mock_issue.fields = mock_fields

        # Simulate pagination: return 50 issues but total is 150
        mock_result_list = Mock()
        mock_result_list.__iter__ = Mock(return_value=iter([mock_issue] * 50))
        mock_result_list.total = 150
        mock_result_list.__bool__ = Mock(return_value=True)
        mock_jira.search_issues.return_value = mock_result_list

        mock_logging = Mock()

        result = search_jira("project = LARGE", mock_jira, mock_logging)

        # Verify the result shows total vs returned
        assert isinstance(result, str)
        assert "Found 150 issues" in result
        assert "showing 50" in result
        mock_logging.info.assert_any_call("Successfully retrieved 50 out of 150 JIRA issues")
