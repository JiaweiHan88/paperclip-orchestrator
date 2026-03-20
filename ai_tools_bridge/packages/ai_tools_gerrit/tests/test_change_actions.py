"""Test cases for the change_actions module."""

from unittest.mock import Mock

import pytest

from ai_tools_gerrit.change_actions import (
    AbandonChangeInput,
    CreateChangeInput,
    RevertChangeInput,
    RevertSubmissionInput,
    SetReadyForReviewInput,
    SetTopicInput,
    SetWorkInProgressInput,
    abandon_change,
    create_change,
    revert_change,
    revert_submission,
    set_ready_for_review,
    set_topic,
    set_work_in_progress,
)


@pytest.fixture
def mock_gerrit() -> Mock:
    return Mock()


# ---------------------------------------------------------------------------
# Input model tests
# ---------------------------------------------------------------------------


class TestSetReadyForReviewInput:
    def test_required_change_id(self) -> None:
        m = SetReadyForReviewInput(change_id="12345")
        assert m.change_id == "12345"


class TestSetWorkInProgressInput:
    def test_required_change_id(self) -> None:
        m = SetWorkInProgressInput(change_id="12345")
        assert m.change_id == "12345"

    def test_message_defaults_to_none(self) -> None:
        m = SetWorkInProgressInput(change_id="1")
        assert m.message is None

    def test_optional_message(self) -> None:
        m = SetWorkInProgressInput(change_id="1", message="Still in progress.")
        assert m.message == "Still in progress."


class TestSetTopicInput:
    def test_required_fields(self) -> None:
        m = SetTopicInput(change_id="12345", topic="my-topic")
        assert m.change_id == "12345"
        assert m.topic == "my-topic"

    def test_empty_topic_allowed(self) -> None:
        m = SetTopicInput(change_id="1", topic="")
        assert m.topic == ""


class TestRevertChangeInput:
    def test_required_change_id(self) -> None:
        m = RevertChangeInput(change_id="12345")
        assert m.change_id == "12345"

    def test_message_defaults_to_none(self) -> None:
        m = RevertChangeInput(change_id="1")
        assert m.message is None


class TestRevertSubmissionInput:
    def test_required_change_id(self) -> None:
        m = RevertSubmissionInput(change_id="12345")
        assert m.change_id == "12345"

    def test_message_optional(self) -> None:
        m = RevertSubmissionInput(change_id="1", message="CI failure.")
        assert m.message == "CI failure."


class TestCreateChangeInput:
    def test_required_fields(self) -> None:
        m = CreateChangeInput(project="my-proj", subject="feat: X", branch="main")
        assert m.project == "my-proj"
        assert m.subject == "feat: X"
        assert m.branch == "main"

    def test_optional_topic_none(self) -> None:
        m = CreateChangeInput(project="p", subject="s", branch="b")
        assert m.topic is None

    def test_optional_status_none(self) -> None:
        m = CreateChangeInput(project="p", subject="s", branch="b")
        assert m.status is None


class TestAbandonChangeInput:
    def test_required_change_id(self) -> None:
        m = AbandonChangeInput(change_id="12345")
        assert m.change_id == "12345"

    def test_message_defaults_to_none(self) -> None:
        m = AbandonChangeInput(change_id="1")
        assert m.message is None


# ---------------------------------------------------------------------------
# set_ready_for_review
# ---------------------------------------------------------------------------


class TestSetReadyForReview:
    def test_returns_confirmation(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        result = set_ready_for_review(change_id="12345", gerrit=mock_gerrit)
        assert "12345" in result
        assert "ready" in result.lower()

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        set_ready_for_review(change_id="55555", gerrit=mock_gerrit)
        call_url = mock_gerrit.post.call_args[0][0]
        assert "55555" in call_url
        assert "ready" in call_url


# ---------------------------------------------------------------------------
# set_work_in_progress
# ---------------------------------------------------------------------------


class TestSetWorkInProgress:
    def test_returns_confirmation(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        result = set_work_in_progress(change_id="12345", gerrit=mock_gerrit)
        assert "12345" in result
        assert "Work-In-Progress" in result or "WIP" in result or "wip" in result.lower()

    def test_calls_wip_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        set_work_in_progress(change_id="55555", gerrit=mock_gerrit)
        call_url = mock_gerrit.post.call_args[0][0]
        assert "55555" in call_url
        assert "wip" in call_url

    def test_payload_with_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        set_work_in_progress(change_id="1", gerrit=mock_gerrit, message="Still working.")
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload == {"message": "Still working."}

    def test_no_payload_without_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = None
        set_work_in_progress(change_id="1", gerrit=mock_gerrit)
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload is None


# ---------------------------------------------------------------------------
# set_topic
# ---------------------------------------------------------------------------


class TestSetTopic:
    def test_returns_new_topic(self, mock_gerrit: Mock) -> None:
        mock_gerrit.put.return_value = "feature/login"
        result = set_topic(change_id="12345", topic="feature/login", gerrit=mock_gerrit)
        assert "feature/login" in result
        assert "12345" in result

    def test_empty_topic_deletion_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.put.return_value = None
        result = set_topic(change_id="12345", topic="", gerrit=mock_gerrit)
        assert "deleted" in result.lower() or "Topic deleted" in result

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.put.return_value = "my-topic"
        set_topic(change_id="55555", topic="my-topic", gerrit=mock_gerrit)
        call_url = mock_gerrit.put.call_args[0][0]
        assert "55555" in call_url
        assert "topic" in call_url

    def test_payload_contains_topic(self, mock_gerrit: Mock) -> None:
        mock_gerrit.put.return_value = "t"
        set_topic(change_id="1", topic="t", gerrit=mock_gerrit)
        payload = mock_gerrit.put.call_args[1]["payload"]
        assert payload == {"topic": "t"}


# ---------------------------------------------------------------------------
# revert_change
# ---------------------------------------------------------------------------


class TestRevertChange:
    def test_returns_new_revert_cl_number(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {"_number": 9999, "subject": "Revert feat: X"}
        result = revert_change(change_id="12345", gerrit=mock_gerrit)
        assert "9999" in result
        assert "12345" in result

    def test_shows_revert_subject(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {
            "_number": 100,
            "subject": "Revert: bad change",
        }
        result = revert_change(change_id="1", gerrit=mock_gerrit)
        assert "Revert: bad change" in result

    def test_fallback_message_when_no_number(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {}
        result = revert_change(change_id="1", gerrit=mock_gerrit)
        assert "1" in result

    def test_calls_revert_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {}
        revert_change(change_id="55555", gerrit=mock_gerrit)
        call_url = mock_gerrit.post.call_args[0][0]
        assert "55555" in call_url
        assert "revert" in call_url

    def test_payload_with_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {}
        revert_change(change_id="1", gerrit=mock_gerrit, message="Unexpected regression.")
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload == {"message": "Unexpected regression."}

    def test_no_payload_without_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {}
        revert_change(change_id="1", gerrit=mock_gerrit)
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload is None


# ---------------------------------------------------------------------------
# revert_submission
# ---------------------------------------------------------------------------


class TestRevertSubmission:
    def test_lists_created_revert_cls(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {
            "revert_changes": [
                {"_number": 200, "subject": "Revert A"},
                {"_number": 201, "subject": "Revert B"},
            ]
        }
        result = revert_submission(change_id="12345", gerrit=mock_gerrit)
        assert "200" in result
        assert "Revert A" in result
        assert "201" in result
        assert "Revert B" in result

    def test_fallback_when_no_revert_changes(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {"revert_changes": []}
        result = revert_submission(change_id="1", gerrit=mock_gerrit)
        assert "1" in result

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {}
        revert_submission(change_id="55555", gerrit=mock_gerrit)
        call_url = mock_gerrit.post.call_args[0][0]
        assert "55555" in call_url
        assert "revert_submission" in call_url


# ---------------------------------------------------------------------------
# create_change
# ---------------------------------------------------------------------------


class TestCreateChange:
    def test_returns_new_change_number(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {
            "_number": 777,
            "subject": "feat: add dark mode",
            "project": "my-project",
            "branch": "main",
        }
        result = create_change(
            project="my-project",
            subject="feat: add dark mode",
            branch="main",
            gerrit=mock_gerrit,
        )
        assert "777" in result

    def test_shows_subject_project_branch(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {
            "_number": 1,
            "subject": "feat: X",
            "project": "proj",
            "branch": "release",
        }
        result = create_change(project="proj", subject="feat: X", branch="release", gerrit=mock_gerrit)
        assert "feat: X" in result
        assert "proj" in result
        assert "release" in result

    def test_fallback_when_no_number(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {}
        result = create_change(project="p", subject="s", branch="b", gerrit=mock_gerrit)
        assert "p" in result

    def test_calls_changes_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {}
        create_change(project="p", subject="s", branch="b", gerrit=mock_gerrit)
        call_url = mock_gerrit.post.call_args[0][0]
        assert "/changes/" in call_url

    def test_payload_required_fields(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {}
        create_change(project="p", subject="s", branch="b", gerrit=mock_gerrit)
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload["project"] == "p"
        assert payload["subject"] == "s"
        assert payload["branch"] == "b"

    def test_topic_in_payload_when_provided(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {}
        create_change(project="p", subject="s", branch="b", gerrit=mock_gerrit, topic="my-topic")
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload["topic"] == "my-topic"

    def test_no_topic_key_when_absent(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {}
        create_change(project="p", subject="s", branch="b", gerrit=mock_gerrit)
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert "topic" not in payload


# ---------------------------------------------------------------------------
# abandon_change
# ---------------------------------------------------------------------------


class TestAbandonChange:
    def test_returns_success_when_abandoned(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {"status": "ABANDONED"}
        result = abandon_change(change_id="12345", gerrit=mock_gerrit)
        assert "12345" in result
        assert "abandoned" in result.lower() or "ABANDONED" in result

    def test_fallback_status_in_output(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {"status": "NEW"}
        result = abandon_change(change_id="1", gerrit=mock_gerrit)
        assert "1" in result

    def test_calls_abandon_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {"status": "ABANDONED"}
        abandon_change(change_id="55555", gerrit=mock_gerrit)
        call_url = mock_gerrit.post.call_args[0][0]
        assert "55555" in call_url
        assert "abandon" in call_url

    def test_payload_with_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {"status": "ABANDONED"}
        abandon_change(change_id="1", gerrit=mock_gerrit, message="Superseded by CL 9999.")
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload == {"message": "Superseded by CL 9999."}

    def test_no_payload_without_message(self, mock_gerrit: Mock) -> None:
        mock_gerrit.post.return_value = {"status": "ABANDONED"}
        abandon_change(change_id="1", gerrit=mock_gerrit)
        payload = mock_gerrit.post.call_args[1]["payload"]
        assert payload is None
