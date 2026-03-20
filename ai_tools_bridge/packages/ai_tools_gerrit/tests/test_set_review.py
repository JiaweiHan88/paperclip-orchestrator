"""Test cases for the set_review module."""

from unittest.mock import Mock

import pytest

from ai_tools_gerrit.set_review import (
    SetReviewInput,
    set_review,
)


@pytest.fixture
def mock_gerrit() -> Mock:
    return Mock()


# ---------------------------------------------------------------------------
# Input model tests
# ---------------------------------------------------------------------------


class TestSetReviewInput:
    def test_defaults(self) -> None:
        m = SetReviewInput(change_id="12345")
        assert m.change_id == "12345"
        assert m.revision_id == "current"
        assert m.labels is None
        assert m.message is None

    def test_all_fields(self) -> None:
        m = SetReviewInput(
            change_id="12345",
            revision_id="2",
            labels={"Code-Review": 2},
            message="LGTM!",
        )
        assert m.revision_id == "2"
        assert m.labels == {"Code-Review": 2}
        assert m.message == "LGTM!"


# ---------------------------------------------------------------------------
# set_review
# ---------------------------------------------------------------------------


class TestSetReview:
    def test_set_labels(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        result = set_review(change_id="12345", gerrit=mock_gerrit, labels={"Code-Review": 2})
        assert "Successfully reviewed" in result
        assert "Code-Review: +2" in result
        mock_gerrit.post.assert_called_once()
        call_args = mock_gerrit.post.call_args
        assert "12345" in call_args[0][0]
        assert call_args[1]["payload"]["labels"] == {"Code-Review": 2}

    def test_set_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        result = set_review(change_id="12345", gerrit=mock_gerrit, message="Looks good!")
        assert "Review message posted" in result
        call_args = mock_gerrit.post.call_args
        assert call_args[1]["payload"]["message"] == "Looks good!"

    def test_set_labels_and_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        result = set_review(
            change_id="12345",
            gerrit=mock_gerrit,
            labels={"Code-Review": 1},
            message="Minor comments",
        )
        assert "Labels set" in result
        assert "Review message posted" in result

    def test_no_input_error(self, mock_gerrit: Mock) -> None:
        result = set_review(change_id="12345", gerrit=mock_gerrit)
        assert "Error" in result
        mock_gerrit.post.assert_not_called()

    def test_specific_revision(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        set_review(change_id="12345", gerrit=mock_gerrit, revision_id="3", labels={"Verified": 1})
        call_url = mock_gerrit.post.call_args[0][0]
        assert "/revisions/3/" in call_url

    def test_negative_vote_formatting(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        result = set_review(change_id="12345", gerrit=mock_gerrit, labels={"Code-Review": -2})
        assert "Code-Review: -2" in result

    def test_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        set_review(change_id="12345", gerrit=mock_gerrit, labels={"Code-Review": 1})
        call_url = mock_gerrit.post.call_args[0][0]
        assert "/changes/12345/revisions/current/review" == call_url
