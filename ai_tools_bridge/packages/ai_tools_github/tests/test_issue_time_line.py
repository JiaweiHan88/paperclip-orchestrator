"""Tests for the issue_time_line module."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from ai_tools_github.issue_time_line import (
    IssueTimeLineInput,
    format_timeline_event,
    get_issue_time_line,
    parse_timestamp,
    should_include_event,
)


class TestIssueTimeLineInput:
    """Test the IssueTimeLineInput model."""

    def test_valid_input(self):
        """Test valid input parameters."""
        input_data = IssueTimeLineInput(
            owner="owner",
            repo="repo",
            limit=50,
            filters={"status": "open"},
            project_name="Test Project",
        )
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.limit == 50
        assert input_data.filters == {"status": "open"}
        assert input_data.project_name == "Test Project"

    def test_default_values(self):
        """Test default values."""
        input_data = IssueTimeLineInput(owner="owner", repo="repo")
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.limit == 100  # default value
        assert input_data.filters == {}  # default value
        assert input_data.from_timestamp is None  # default value
        assert input_data.to_timestamp is None  # default value
        assert input_data.project_name is None  # default value

    def test_optional_project_name(self):
        """Test that project_name is optional."""
        # Test with project_name
        input_with_project = IssueTimeLineInput(owner="owner", repo="repo", project_name="Development Board")
        assert input_with_project.project_name == "Development Board"

        # Test without project_name
        input_without_project = IssueTimeLineInput(owner="owner", repo="repo")
        assert input_without_project.project_name is None

    def test_all_fields(self):
        """Test all fields including from_timestamp, to_timestamp and project_name."""
        input_data = IssueTimeLineInput(
            owner="owner",
            repo="repo",
            limit=50,
            filters={"status": "open", "assignee": "testuser", "labels": ["bug"]},
            from_timestamp="2025-11-18T20:18:55Z",
            to_timestamp="2025-11-20T20:18:55Z",
            project_name="Development Board",
        )
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.limit == 50
        assert input_data.filters == {"status": "open", "assignee": "testuser", "labels": ["bug"]}
        assert input_data.from_timestamp == "2025-11-18T20:18:55Z"
        assert input_data.to_timestamp == "2025-11-20T20:18:55Z"
        assert input_data.project_name == "Development Board"


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

    def test_should_include_event(self):
        """Test event filtering by timestamp."""
        # Test without filters
        assert should_include_event("2025-11-18T20:18:55Z", None, None) is True

        # Test with from_timestamp only - event should be included
        assert should_include_event("2025-11-18T20:18:55Z", "2025-11-18T00:00:00Z", None) is True

        # Test with from_timestamp only - event should be excluded (before from)
        assert should_include_event("2025-11-17T20:18:55Z", "2025-11-18T00:00:00Z", None) is False

        # Test with to_timestamp only - event should be included (before to)
        assert should_include_event("2025-11-18T20:18:55Z", None, "2025-11-19T00:00:00Z") is True

        # Test with to_timestamp only - event should be excluded (after to)
        assert should_include_event("2025-11-20T20:18:55Z", None, "2025-11-19T00:00:00Z") is False

        # Test with both timestamps - event in range
        assert should_include_event("2025-11-18T12:00:00Z", "2025-11-18T00:00:00Z", "2025-11-19T00:00:00Z") is True

        # Test with both timestamps - event before range
        assert should_include_event("2025-11-17T12:00:00Z", "2025-11-18T00:00:00Z", "2025-11-19T00:00:00Z") is False

        # Test with both timestamps - event after range
        assert should_include_event("2025-11-20T12:00:00Z", "2025-11-18T00:00:00Z", "2025-11-19T00:00:00Z") is False


class TestGetIssueTimeLine:
    """Test the main get_issue_time_line function."""

    @patch("ai_tools_github.issue_time_line.logger")
    def test_get_issue_time_line_basic(self, mock_logger):
        """Test basic functionality of get_issue_time_line."""
        mock_github = Mock()
        mock_github.query.return_value = {
            "search": {
                "issueCount": 1,
                "nodes": [
                    {
                        "title": "Test Issue",
                        "number": 1,
                        "url": "https://github.example.com/owner/repo/issues/1",
                        "body": "Test issue body",
                        "createdAt": "2025-11-18T20:18:55Z",
                        "state": "OPEN",
                        "labels": {"nodes": [{"name": "bug"}]},
                        "timelineItems": {"nodes": []},
                        "projectItems": {"nodes": []},
                    }
                ],
            }
        }

        result = get_issue_time_line(owner="owner", repo="repo", github=mock_github, limit=1)

        assert "Test Issue" in result
        assert "issue" in result.lower()
        assert "OPEN" in result
        assert "bug" in result
        mock_github.query.assert_called_once()

    def test_get_issue_time_line_repository_not_found(self):
        """Test handling when repository data is not found."""
        mock_github = Mock()
        mock_github.query.return_value = {"search": {"nodes": []}}  # No issues found

        result = get_issue_time_line("owner", "nonexistent", github=mock_github)

        assert "No issues found" in result

    def test_get_issue_time_line_graphql_errors(self):
        """Test handling of GraphQL errors."""
        mock_github = Mock()
        mock_github.query.return_value = {"errors": [{"message": "API rate limit exceeded"}]}

        result = get_issue_time_line("owner", "repo", github=mock_github)

        assert "Error fetching issues" in result

    def test_get_issue_time_line_exception_handling(self):
        """Test exception handling in get_issue_time_line."""
        mock_github = Mock()
        mock_github.query.side_effect = Exception("Network timeout")

        result = get_issue_time_line("owner", "repo", github=mock_github)

        assert "Error:" in result

    def test_get_issue_time_line_empty_issues(self):
        """Test repository with no issues."""
        mock_github = Mock()
        mock_github.query.return_value = {"search": {"issueCount": 0, "nodes": []}}

        result = get_issue_time_line("owner", "repo", github=mock_github)

        assert "No issues found" in result
