"""Test cases for the comments module."""

from unittest.mock import Mock

import pytest

from ai_tools_gerrit.comments import (
    ListChangeCommentsInput,
    PostReviewCommentInput,
    list_change_comments,
    post_review_comment,
)


@pytest.fixture
def mock_gerrit() -> Mock:
    return Mock()


# ---------------------------------------------------------------------------
# Input model tests
# ---------------------------------------------------------------------------


class TestListChangeCommentsInput:
    def test_required_change_id(self) -> None:
        m = ListChangeCommentsInput(change_id="12345")
        assert m.change_id == "12345"


class TestPostReviewCommentInput:
    def test_required_fields(self) -> None:
        m = PostReviewCommentInput(
            change_id="12345",
            file_path="src/main.py",
            line_number=42,
            message="Please fix this.",
        )
        assert m.change_id == "12345"
        assert m.file_path == "src/main.py"
        assert m.line_number == 42
        assert m.message == "Please fix this."

    def test_unresolved_defaults_true(self) -> None:
        m = PostReviewCommentInput(change_id="1", file_path="f.py", line_number=1, message="x")
        assert m.unresolved is True

    def test_labels_default_none(self) -> None:
        m = PostReviewCommentInput(change_id="1", file_path="f.py", line_number=1, message="x")
        assert m.labels is None

    def test_optional_labels(self) -> None:
        m = PostReviewCommentInput(
            change_id="1",
            file_path="f.py",
            line_number=1,
            message="x",
            labels={"Code-Review": -1},
        )
        assert m.labels == {"Code-Review": -1}


# ---------------------------------------------------------------------------
# list_change_comments
# ---------------------------------------------------------------------------


class TestListChangeComments:
    def test_no_comments_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {}
        result = list_change_comments(change_id="12345", gerrit=mock_gerrit)
        assert "No comments found" in result
        assert "12345" in result

    def test_shows_file_path(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "src/main.py": [
                {
                    "line": 10,
                    "author": {"name": "Alice"},
                    "updated": "2025-01-01",
                    "message": "Fix this",
                    "unresolved": True,
                }
            ]
        }
        result = list_change_comments(change_id="12345", gerrit=mock_gerrit)
        assert "src/main.py" in result

    def test_shows_author_name(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "foo.py": [
                {
                    "line": 5,
                    "author": {"name": "Bob"},
                    "updated": "2025-01-02",
                    "message": "LGTM",
                    "unresolved": False,
                }
            ]
        }
        result = list_change_comments(change_id="1", gerrit=mock_gerrit)
        assert "Bob" in result

    def test_shows_comment_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "bar.py": [
                {
                    "line": 1,
                    "author": {"name": "Carol"},
                    "updated": "2025-01-03",
                    "message": "Please refactor this section.",
                    "unresolved": True,
                }
            ]
        }
        result = list_change_comments(change_id="1", gerrit=mock_gerrit)
        assert "Please refactor this section." in result

    def test_shows_unresolved_status(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "f.py": [
                {
                    "line": 1,
                    "author": {"name": "X"},
                    "updated": "2025-01-01",
                    "message": "check",
                    "unresolved": True,
                }
            ]
        }
        result = list_change_comments(change_id="1", gerrit=mock_gerrit)
        assert "UNRESOLVED" in result

    def test_shows_resolved_status(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {
            "f.py": [
                {
                    "line": 1,
                    "author": {"name": "X"},
                    "updated": "2025-01-01",
                    "message": "done",
                    "unresolved": False,
                }
            ]
        }
        result = list_change_comments(change_id="1", gerrit=mock_gerrit)
        assert "RESOLVED" in result

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = {}
        list_change_comments(change_id="55555", gerrit=mock_gerrit)
        mock_gerrit.get.assert_called_once_with("/changes/55555/comments")


# ---------------------------------------------------------------------------
# post_review_comment
# ---------------------------------------------------------------------------


class TestPostReviewComment:
    def test_returns_confirmation(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        result = post_review_comment(
            change_id="12345",
            file_path="src/main.py",
            line_number=42,
            message="Needs refactoring.",
            gerrit=mock_gerrit,
        )
        assert "12345" in result
        assert "src/main.py" in result
        assert "42" in result

    def test_calls_review_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        post_review_comment(
            change_id="99999",
            file_path="foo.py",
            line_number=1,
            message="x",
            gerrit=mock_gerrit,
        )
        call_url = mock_gerrit.post.call_args[0][0]
        assert "99999" in call_url
        assert "review" in call_url

    def test_payload_contains_comment(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        post_review_comment(
            change_id="1",
            file_path="a.py",
            line_number=10,
            message="my comment",
            gerrit=mock_gerrit,
        )
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert "a.py" in payload["comments"]
        comment = payload["comments"]["a.py"][0]
        assert comment["line"] == 10
        assert comment["message"] == "my comment"

    def test_unresolved_flag_in_payload(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        post_review_comment(
            change_id="1",
            file_path="a.py",
            line_number=1,
            message="x",
            gerrit=mock_gerrit,
            unresolved=False,
        )
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload["comments"]["a.py"][0]["unresolved"] is False

    def test_labels_included_when_provided(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        post_review_comment(
            change_id="1",
            file_path="a.py",
            line_number=1,
            message="x",
            gerrit=mock_gerrit,
            labels={"Code-Review": -1},
        )
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload["labels"] == {"Code-Review": -1}

    def test_no_labels_key_when_absent(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        post_review_comment(
            change_id="1",
            file_path="a.py",
            line_number=1,
            message="x",
            gerrit=mock_gerrit,
        )
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert "labels" not in payload
