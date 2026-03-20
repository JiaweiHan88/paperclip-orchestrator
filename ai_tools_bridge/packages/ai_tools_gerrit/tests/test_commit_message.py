"""Test cases for the commit_message module."""

from unittest.mock import Mock

import pytest

from ai_tools_gerrit.commit_message import (
    GetBugsFromClInput,
    GetCommitMessageInput,
    extract_bugs,
    get_bugs_from_cl,
    get_commit_message,
)


@pytest.fixture
def mock_gerrit() -> Mock:
    return Mock()


# ---------------------------------------------------------------------------
# extract_bugs
# ---------------------------------------------------------------------------


class TestExtractBugs:
    def test_bug_footer(self) -> None:
        assert extract_bugs("Fix something\n\nBug: 12345") == {"12345"}

    def test_fixes_footer(self) -> None:
        assert extract_bugs("Fix something\n\nFixes: 67890") == {"67890"}

    def test_closes_footer(self) -> None:
        assert extract_bugs("Fix something\n\nCloses: 11111") == {"11111"}

    def test_b_slash_prefix(self) -> None:
        assert extract_bugs("Fixes: b/12345") == {"12345"}

    def test_multiple_bugs_in_footer(self) -> None:
        assert extract_bugs("Bug: 111, b/222") == {"111", "222"}

    def test_inline_b_slash_mention(self) -> None:
        msg = "This resolves b/99999 which caused a crash."
        assert extract_bugs(msg) == {"99999"}

    def test_mixed_footer_and_inline(self) -> None:
        msg = "Patch for b/100\n\nBug: 200, b/300"
        assert extract_bugs(msg) == {"100", "200", "300"}

    def test_no_bugs_returns_empty_set(self) -> None:
        assert extract_bugs("Refactoring only, no bugs") == set()

    def test_case_insensitive_footer(self) -> None:
        assert extract_bugs("bug: 55555") == {"55555"}

    def test_whitespace_in_footer(self) -> None:
        assert extract_bugs("Bug : 77777") == set()  # no space before colon matches


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class TestGetCommitMessageInput:
    def test_required_change_id(self) -> None:
        m = GetCommitMessageInput(change_id="12345")
        assert m.change_id == "12345"


class TestGetBugsFromClInput:
    def test_required_change_id(self) -> None:
        m = GetBugsFromClInput(change_id="Iabc123")
        assert m.change_id == "Iabc123"


# ---------------------------------------------------------------------------
# get_commit_message
# ---------------------------------------------------------------------------


class TestGetCommitMessage:
    def test_formats_subject_and_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "subject": "feat: add dark mode",
            "message": "feat: add dark mode\n\nImplemented dark mode toggle.",
        }
        result = get_commit_message(change_id="12345", gerrit=mock_gerrit)
        assert "feat: add dark mode" in result
        assert "Implemented dark mode toggle." in result

    def test_includes_footers(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "subject": "fix: crash",
            "message": "fix: crash\n\nBug: 99",
            "footers": {"Bug": "99", "Change-Id": "Iabc"},
        }
        result = get_commit_message(change_id="12345", gerrit=mock_gerrit)
        assert "Bug" in result
        assert "99" in result
        assert "Change-Id" in result

    def test_no_footers_when_absent(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "subject": "chore: cleanup",
            "message": "chore: cleanup",
        }
        result = get_commit_message(change_id="12345", gerrit=mock_gerrit)
        assert "Footers" not in result

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {"subject": "s", "message": "s"}
        get_commit_message(change_id="99999", gerrit=mock_gerrit)
        mock_gerrit.get.assert_called_once_with("/changes/99999/revisions/current/commit")


# ---------------------------------------------------------------------------
# get_bugs_from_cl
# ---------------------------------------------------------------------------


class TestGetBugsFromCl:
    def test_returns_bug_ids(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {"message": "fix: null pointer\n\nBug: 42, b/7"}
        result = get_bugs_from_cl(change_id="12345", gerrit=mock_gerrit)
        assert "42" in result
        assert "7" in result

    def test_no_bugs_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {"message": "refactor: cleanup code"}
        result = get_bugs_from_cl(change_id="12345", gerrit=mock_gerrit)
        assert "No bug IDs found" in result

    def test_empty_commit_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {}
        result = get_bugs_from_cl(change_id="12345", gerrit=mock_gerrit)
        assert "No commit message found" in result

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {"message": "no bugs"}
        get_bugs_from_cl(change_id="55555", gerrit=mock_gerrit)
        mock_gerrit.get.assert_called_once_with("/changes/55555/revisions/current/commit")
