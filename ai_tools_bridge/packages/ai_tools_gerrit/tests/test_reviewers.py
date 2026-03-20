"""Test cases for the reviewers module."""

from unittest.mock import Mock

import pytest

from ai_tools_gerrit.reviewers import (
    AddReviewerInput,
    SuggestReviewersInput,
    add_reviewer,
    suggest_reviewers,
)


@pytest.fixture
def mock_gerrit() -> Mock:
    return Mock()


# ---------------------------------------------------------------------------
# Input model tests
# ---------------------------------------------------------------------------


class TestAddReviewerInput:
    def test_required_fields(self) -> None:
        m = AddReviewerInput(change_id="12345", reviewer="alice@example.com")
        assert m.change_id == "12345"
        assert m.reviewer == "alice@example.com"

    def test_state_defaults_to_reviewer(self) -> None:
        m = AddReviewerInput(change_id="1", reviewer="alice@example.com")
        assert m.state == "REVIEWER"

    def test_state_cc(self) -> None:
        m = AddReviewerInput(change_id="1", reviewer="bob@example.com", state="CC")
        assert m.state == "CC"


class TestSuggestReviewersInput:
    def test_required_fields(self) -> None:
        m = SuggestReviewersInput(change_id="12345", query="jane")
        assert m.change_id == "12345"
        assert m.query == "jane"

    def test_optional_defaults(self) -> None:
        m = SuggestReviewersInput(change_id="1", query="x")
        assert m.limit is None
        assert m.exclude_groups is False
        assert m.reviewer_state is None


# ---------------------------------------------------------------------------
# add_reviewer
# ---------------------------------------------------------------------------


class TestAddReviewer:
    def test_returns_confirmation(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        result = add_reviewer(change_id="12345", reviewer="alice@example.com", gerrit=mock_gerrit)
        assert "alice@example.com" in result
        assert "12345" in result

    def test_default_state_reviewer(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        result = add_reviewer(change_id="1", reviewer="bob@example.com", gerrit=mock_gerrit)
        assert "REVIEWER" in result

    def test_cc_state(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        result = add_reviewer(change_id="1", reviewer="carol@example.com", gerrit=mock_gerrit, state="CC")
        assert "CC" in result

    def test_invalid_state_raises(self, mock_gerrit: Mock) -> None:
        with pytest.raises(ValueError, match="Invalid state"):
            add_reviewer(change_id="1", reviewer="x@example.com", gerrit=mock_gerrit, state="INVALID")

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        add_reviewer(change_id="55555", reviewer="dev@example.com", gerrit=mock_gerrit)
        call_url = mock_gerrit.post.call_args[0][0]
        assert "55555" in call_url
        assert "reviewers" in call_url

    def test_payload_contains_reviewer_and_state(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        add_reviewer(change_id="1", reviewer="dev@example.com", gerrit=mock_gerrit, state="CC")
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload["reviewer"] == "dev@example.com"
        assert payload["state"] == "CC"

    def test_state_uppercased_in_payload(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        add_reviewer(change_id="1", reviewer="dev@example.com", gerrit=mock_gerrit, state="reviewer")
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload["state"] == "REVIEWER"


# ---------------------------------------------------------------------------
# suggest_reviewers
# ---------------------------------------------------------------------------


class TestSuggestReviewers:
    def test_lists_account_suggestions(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"account": {"name": "Alice Smith", "email": "alice@example.com"}},
        ]
        result = suggest_reviewers(change_id="12345", query="alice", gerrit=mock_gerrit)
        assert "Alice Smith" in result
        assert "alice@example.com" in result

    def test_lists_group_suggestions(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"group": {"name": "backend-team"}},
        ]
        result = suggest_reviewers(change_id="12345", query="backend", gerrit=mock_gerrit)
        assert "backend-team" in result

    def test_no_results_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        result = suggest_reviewers(change_id="12345", query="zzz", gerrit=mock_gerrit)
        assert "No reviewers found" in result

    def test_passes_query_param(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        suggest_reviewers(change_id="1", query="jane", gerrit=mock_gerrit)
        call_params = mock_gerrit.get.call_args[1]["params"]
        assert call_params["q"] == "jane"

    def test_passes_limit_param(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        suggest_reviewers(change_id="1", query="x", gerrit=mock_gerrit, limit=5)
        call_params = mock_gerrit.get.call_args[1]["params"]
        assert call_params["n"] == 5

    def test_no_limit_param_when_none(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        suggest_reviewers(change_id="1", query="x", gerrit=mock_gerrit)
        call_params = mock_gerrit.get.call_args[1]["params"]
        assert "n" not in call_params

    def test_exclude_groups_param(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        suggest_reviewers(change_id="1", query="x", gerrit=mock_gerrit, exclude_groups=True)
        call_params = mock_gerrit.get.call_args[1]["params"]
        assert "exclude-groups" in call_params

    def test_reviewer_state_param(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        suggest_reviewers(change_id="1", query="x", gerrit=mock_gerrit, reviewer_state="REVIEWER")
        call_params = mock_gerrit.get.call_args[1]["params"]
        assert call_params["reviewer-state"] == "REVIEWER"

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        suggest_reviewers(change_id="55555", query="alice", gerrit=mock_gerrit)
        call_url = mock_gerrit.get.call_args[0][0]
        assert "55555" in call_url
        assert "suggest_reviewers" in call_url
