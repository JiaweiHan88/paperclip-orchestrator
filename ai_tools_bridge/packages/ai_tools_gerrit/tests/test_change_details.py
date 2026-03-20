"""Test cases for the change_details module."""

from unittest.mock import Mock

import pytest

from ai_tools_gerrit.change_details import (
    ChangesSubmittedTogetherInput,
    GetChangeDetailsInput,
    changes_submitted_together,
    get_change_details,
)


@pytest.fixture
def mock_gerrit() -> Mock:
    return Mock()


@pytest.fixture
def sample_detail() -> dict:  # type: ignore[type-arg]
    return {
        "_number": 12345,
        "subject": "feat: new feature",
        "owner": {"email": "dev@example.com"},
        "status": "NEW",
        "current_revision": "abc",
        "revisions": {"abc": {"commit": {"message": "feat: new feature\n\nBug: 42"}}},
        "reviewers": {"REVIEWER": [{"_account_id": 1, "email": "rev@example.com"}]},
        "labels": {"Code-Review": {"all": [{"_account_id": 1, "value": 2}]}},
        "messages": [
            {
                "_revision_number": 1,
                "date": "2025-01-01",
                "author": {"name": "Bot"},
                "message": "Patch Set 1: build ok",
            },
            {"_revision_number": 2, "date": "2025-01-02", "author": {"name": "Alice"}, "message": "LGTM"},
        ],
    }


# ---------------------------------------------------------------------------
# Input model tests
# ---------------------------------------------------------------------------


class TestGetChangeDetailsInput:
    def test_required_change_id(self) -> None:
        m = GetChangeDetailsInput(change_id="12345")
        assert m.change_id == "12345"

    def test_options_default_none(self) -> None:
        m = GetChangeDetailsInput(change_id="12345")
        assert m.options is None


class TestChangesSubmittedTogetherInput:
    def test_required_change_id(self) -> None:
        m = ChangesSubmittedTogetherInput(change_id="99999")
        assert m.change_id == "99999"


# ---------------------------------------------------------------------------
# get_change_details
# ---------------------------------------------------------------------------


class TestGetChangeDetails:
    def test_shows_cl_number_and_subject(self, mock_gerrit: Mock, sample_detail: dict) -> None:  # type: ignore[type-arg]
        mock_gerrit.get.return_value = sample_detail
        result = get_change_details(change_id="12345", gerrit=mock_gerrit)
        assert "12345" in result
        assert "feat: new feature" in result

    def test_shows_owner_email(self, mock_gerrit: Mock, sample_detail: dict) -> None:  # type: ignore[type-arg]
        mock_gerrit.get.return_value = sample_detail
        result = get_change_details(change_id="12345", gerrit=mock_gerrit)
        assert "dev@example.com" in result

    def test_shows_status(self, mock_gerrit: Mock, sample_detail: dict) -> None:  # type: ignore[type-arg]
        mock_gerrit.get.return_value = sample_detail
        result = get_change_details(change_id="12345", gerrit=mock_gerrit)
        assert "NEW" in result

    def test_shows_reviewers(self, mock_gerrit: Mock, sample_detail: dict) -> None:  # type: ignore[type-arg]
        mock_gerrit.get.return_value = sample_detail
        result = get_change_details(change_id="12345", gerrit=mock_gerrit)
        assert "rev@example.com" in result

    def test_shows_vote_values(self, mock_gerrit: Mock, sample_detail: dict) -> None:  # type: ignore[type-arg]
        mock_gerrit.get.return_value = sample_detail
        result = get_change_details(change_id="12345", gerrit=mock_gerrit)
        assert "Code-Review" in result
        assert "+2" in result

    def test_shows_bug_ids_from_commit_message(self, mock_gerrit: Mock, sample_detail: dict) -> None:  # type: ignore[type-arg]
        mock_gerrit.get.return_value = sample_detail
        result = get_change_details(change_id="12345", gerrit=mock_gerrit)
        assert "42" in result

    def test_shows_recent_messages(self, mock_gerrit: Mock, sample_detail: dict) -> None:  # type: ignore[type-arg]
        mock_gerrit.get.return_value = sample_detail
        result = get_change_details(change_id="12345", gerrit=mock_gerrit)
        assert "Alice" in result
        assert "LGTM" in result

    def test_no_reviewers_section_when_absent(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "_number": 1,
            "subject": "s",
            "owner": {"email": "a@b.com"},
            "status": "NEW",
        }
        result = get_change_details(change_id="1", gerrit=mock_gerrit)
        assert "Reviewers" not in result

    def test_default_options_used(self, mock_gerrit: Mock, sample_detail: dict) -> None:  # type: ignore[type-arg]
        mock_gerrit.get.return_value = sample_detail
        get_change_details(change_id="12345", gerrit=mock_gerrit)
        call_params = mock_gerrit.get.call_args[1]["params"]
        assert "CURRENT_REVISION" in call_params["o"]
        assert "CURRENT_COMMIT" in call_params["o"]
        assert "DETAILED_LABELS" in call_params["o"]

    def test_extra_options_merged(self, mock_gerrit: Mock, sample_detail: dict) -> None:  # type: ignore[type-arg]
        mock_gerrit.get.return_value = sample_detail
        get_change_details(change_id="12345", gerrit=mock_gerrit, options=["MESSAGES"])
        call_params = mock_gerrit.get.call_args[1]["params"]
        assert "MESSAGES" in call_params["o"]
        assert "CURRENT_REVISION" in call_params["o"]

    def test_shows_project_and_branch(self, mock_gerrit: Mock, sample_detail: dict) -> None:  # type: ignore[type-arg]
        sample_detail["project"] = "my-project"
        sample_detail["branch"] = "main"
        mock_gerrit.get.return_value = sample_detail
        result = get_change_details(change_id="12345", gerrit=mock_gerrit)
        assert "my-project" in result
        assert "main" in result

    def test_shows_last_10_messages(self, mock_gerrit: Mock) -> None:
        messages = [
            {"_revision_number": i, "date": f"2025-01-{i:02d}", "author": {"name": f"User{i}"}, "message": f"Msg {i}"}
            for i in range(1, 13)
        ]
        mock_gerrit.get.return_value = {
            "_number": 1,
            "subject": "s",
            "owner": {"email": "a@b.com"},
            "status": "NEW",
            "messages": messages,
        }
        result = get_change_details(change_id="1", gerrit=mock_gerrit)
        # Should show messages 3-12 (last 10), not 1-2
        assert "(User3)" in result
        assert "(User12)" in result
        # User1 and User2 should be excluded (only last 10 of 12)
        assert "(User1)" not in result
        assert "(User2)" not in result

    def test_truncates_long_messages(self, mock_gerrit: Mock) -> None:
        long_msg = "x" * 300
        mock_gerrit.get.return_value = {
            "_number": 1,
            "subject": "s",
            "owner": {"email": "a@b.com"},
            "status": "NEW",
            "messages": [
                {"_revision_number": 1, "date": "2025-01-01", "author": {"name": "Bot"}, "message": long_msg},
            ],
        }
        result = get_change_details(change_id="1", gerrit=mock_gerrit)
        assert "..." in result
        assert long_msg not in result

    def test_shows_label_approved_rejected(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "_number": 1,
            "subject": "s",
            "owner": {"email": "a@b.com"},
            "status": "NEW",
            "labels": {
                "Code-Review": {"approved": {"name": "Alice"}, "all": []},
                "Verified": {"rejected": {"name": "CI"}, "all": []},
            },
        }
        result = get_change_details(change_id="1", gerrit=mock_gerrit)
        assert "Approved by Alice" in result
        assert "Rejected by CI" in result

    def test_shows_revisions(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "_number": 1,
            "subject": "s",
            "owner": {"email": "a@b.com"},
            "status": "NEW",
            "current_revision": "abc123",
            "revisions": {
                "abc123": {"_number": 2, "kind": "REWORK", "commit": {"message": "s"}},
                "def456": {"_number": 1, "kind": "REWORK"},
            },
        }
        result = get_change_details(change_id="1", gerrit=mock_gerrit)
        assert "PS 1" in result
        assert "PS 2" in result
        assert "REWORK" in result


# ---------------------------------------------------------------------------
# changes_submitted_together
# ---------------------------------------------------------------------------


class TestChangesSubmittedTogether:
    def test_lists_related_changes(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "changes": [
                {"_number": 1, "subject": "Part 1"},
                {"_number": 2, "subject": "Part 2"},
            ],
            "non_visible_changes": 0,
        }
        result = changes_submitted_together(change_id="1", gerrit=mock_gerrit)
        assert "1" in result
        assert "Part 1" in result
        assert "2" in result
        assert "Part 2" in result

    def test_shows_non_visible_count(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "changes": [{"_number": 1, "subject": "s"}],
            "non_visible_changes": 3,
        }
        result = changes_submitted_together(change_id="1", gerrit=mock_gerrit)
        assert "3" in result

    def test_empty_response_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {}
        result = changes_submitted_together(change_id="1", gerrit=mock_gerrit)
        assert "submitted by itself" in result

    def test_empty_list_response(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        result = changes_submitted_together(change_id="1", gerrit=mock_gerrit)
        assert "submitted by itself" in result

    def test_list_response_format(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"_number": 10, "subject": "A"},
            {"_number": 11, "subject": "B"},
        ]
        result = changes_submitted_together(change_id="10", gerrit=mock_gerrit)
        assert "10" in result
        assert "11" in result

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        changes_submitted_together(change_id="55555", gerrit=mock_gerrit)
        mock_gerrit.get.assert_called_once_with("/changes/55555/submitted_together", params=None)
