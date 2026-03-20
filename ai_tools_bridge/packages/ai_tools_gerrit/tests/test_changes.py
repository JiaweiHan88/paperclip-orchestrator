"""Test cases for the changes module."""

from unittest.mock import Mock

import pytest

from ai_tools_gerrit.changes import (
    GetMostRecentClInput,
    QueryChangesByDateInput,
    QueryChangesInput,
    get_most_recent_cl,
    query_changes,
    query_changes_by_date,
)


@pytest.fixture
def mock_gerrit() -> Mock:
    return Mock()


# ---------------------------------------------------------------------------
# Input model tests
# ---------------------------------------------------------------------------


class TestQueryChangesInput:
    def test_required_query_field(self) -> None:
        m = QueryChangesInput(query="status:open")
        assert m.query == "status:open"

    def test_optional_fields_default_to_none(self) -> None:
        m = QueryChangesInput(query="is:reviewer")
        assert m.limit is None
        assert m.options is None

    def test_with_all_fields(self) -> None:
        m = QueryChangesInput(query="owner:me", limit=10, options=["CURRENT_REVISION"])
        assert m.limit == 10
        assert m.options == ["CURRENT_REVISION"]


class TestQueryChangesByDateInput:
    def test_required_fields(self) -> None:
        m = QueryChangesByDateInput(start_date="2025-01-01", end_date="2025-01-31")
        assert m.start_date == "2025-01-01"
        assert m.end_date == "2025-01-31"
        assert m.status == "merged"

    def test_optional_fields(self) -> None:
        m = QueryChangesByDateInput(
            start_date="2025-01-01",
            end_date="2025-01-31",
            status="open",
            project="my-project",
            message_substring="fix:",
            limit=50,
        )
        assert m.status == "open"
        assert m.project == "my-project"
        assert m.message_substring == "fix:"
        assert m.limit == 50


class TestGetMostRecentClInput:
    def test_required_user_field(self) -> None:
        m = GetMostRecentClInput(user="jane@example.com")
        assert m.user == "jane@example.com"


# ---------------------------------------------------------------------------
# Function tests
# ---------------------------------------------------------------------------


class TestQueryChanges:
    def test_returns_formatted_list(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"_number": 101, "subject": "Fix bug", "updated": "2025-01-02", "work_in_progress": False},
            {"_number": 100, "subject": "Add feature", "updated": "2025-01-01", "work_in_progress": False},
        ]
        result = query_changes(query="status:open", gerrit=mock_gerrit)
        assert "101" in result
        assert "Fix bug" in result
        assert "100" in result
        assert "Add feature" in result

    def test_wip_prefix_added(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"_number": 50, "subject": "Draft change", "updated": "2025-01-01", "work_in_progress": True},
        ]
        result = query_changes(query="is:wip", gerrit=mock_gerrit)
        assert "[WIP]" in result

    def test_no_wip_prefix_for_ready(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"_number": 51, "subject": "Ready change", "updated": "2025-01-01", "work_in_progress": False},
        ]
        result = query_changes(query="status:open", gerrit=mock_gerrit)
        assert "[WIP]" not in result

    def test_empty_results(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        result = query_changes(query="status:open project:nonexistent", gerrit=mock_gerrit)
        assert "No changes found" in result

    def test_sorted_by_date_descending(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"_number": 1, "subject": "Old", "updated": "2025-01-01", "work_in_progress": False},
            {"_number": 2, "subject": "New", "updated": "2025-01-10", "work_in_progress": False},
        ]
        result = query_changes(query="status:open", gerrit=mock_gerrit)
        # Newer (2) should appear before older (1)
        assert result.index("2") < result.index("1")

    def test_passes_limit_param(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        query_changes(query="status:open", gerrit=mock_gerrit, limit=25)
        call_params = mock_gerrit.get.call_args[1]["params"]
        assert call_params["n"] == 25

    def test_passes_options_param(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        query_changes(query="status:open", gerrit=mock_gerrit, options=["CURRENT_REVISION"])
        call_params = mock_gerrit.get.call_args[1]["params"]
        assert call_params["o"] == ["CURRENT_REVISION"]

    def test_found_count_in_output(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"_number": 1, "subject": "A", "updated": "2025-01-01", "work_in_progress": False},
        ]
        result = query_changes(query="status:open", gerrit=mock_gerrit)
        assert "Found 1 changes" in result

    def test_more_changes_hint_shown(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"_number": 1, "subject": "A", "updated": "2025-01-01", "work_in_progress": False, "_more_changes": True},
        ]
        result = query_changes(query="status:open", gerrit=mock_gerrit)
        assert "More changes available" in result

    def test_no_more_changes_hint_when_absent(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"_number": 1, "subject": "A", "updated": "2025-01-01", "work_in_progress": False},
        ]
        result = query_changes(query="status:open", gerrit=mock_gerrit)
        assert "More changes available" not in result


class TestQueryChangesByDate:
    def test_invalid_start_date(self, mock_gerrit: Mock) -> None:
        result = query_changes_by_date(start_date="not-a-date", end_date="2025-01-31", gerrit=mock_gerrit)
        assert "Invalid date format" in result

    def test_invalid_end_date(self, mock_gerrit: Mock) -> None:
        result = query_changes_by_date(start_date="2025-01-01", end_date="31/01/2025", gerrit=mock_gerrit)
        assert "Invalid date format" in result

    def test_builds_correct_query(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        query_changes_by_date(start_date="2025-01-01", end_date="2025-01-31", gerrit=mock_gerrit)
        call_params = mock_gerrit.get.call_args[1]["params"]
        q = call_params["q"]
        assert "status:merged" in q
        assert "after:2025-01-01" in q
        assert "before:2025-02-01" in q  # end+1 for exclusive range

    def test_project_filter_added(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        query_changes_by_date(
            start_date="2025-01-01",
            end_date="2025-01-31",
            gerrit=mock_gerrit,
            project="my-project",
        )
        q = mock_gerrit.get.call_args[1]["params"]["q"]
        assert "project:my-project" in q

    def test_message_substring_filter_added(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        query_changes_by_date(
            start_date="2025-01-01",
            end_date="2025-01-31",
            gerrit=mock_gerrit,
            message_substring="fix:",
        )
        q = mock_gerrit.get.call_args[1]["params"]["q"]
        assert 'message:"fix:"' in q

    def test_custom_status(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        query_changes_by_date(start_date="2025-01-01", end_date="2025-01-31", gerrit=mock_gerrit, status="open")
        q = mock_gerrit.get.call_args[1]["params"]["q"]
        assert "status:open" in q


class TestGetMostRecentCl:
    def test_returns_most_recent_change(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [{"_number": 999, "subject": "Latest fix", "work_in_progress": False}]
        result = get_most_recent_cl(user="alice@example.com", gerrit=mock_gerrit)
        assert "999" in result
        assert "Latest fix" in result
        assert "alice@example.com" in result

    def test_wip_flag_shown(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [{"_number": 998, "subject": "WIP change", "work_in_progress": True}]
        result = get_most_recent_cl(user="bob", gerrit=mock_gerrit)
        assert "[WIP]" in result

    def test_no_changes_found(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        result = get_most_recent_cl(user="unknown@example.com", gerrit=mock_gerrit)
        assert "No changes found" in result
        assert "unknown@example.com" in result

    def test_queries_with_limit_1(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        get_most_recent_cl(user="alice", gerrit=mock_gerrit)
        call_params = mock_gerrit.get.call_args[1]["params"]
        assert call_params["n"] == 1
