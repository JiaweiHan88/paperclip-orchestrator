"""Test cases for pull_request_actions module."""

from unittest.mock import Mock

import pytest
from ai_tools_github.github_types import Reaction
from ai_tools_github.models.pull_request import PullRequest as GitauditPullRequest

from ai_tools_github.pull_request_actions import (
    AddCommentToPullRequestInput,
    AddLabelToPullRequestInput,
    CreateReactionToPullRequestCommentInput,
    RemoveLabelFromPullRequestInput,
    add_comment_to_pull_request,
    add_label_to_pull_request,
    create_reaction_to_pull_request_comment,
    remove_label_from_pull_request,
)


@pytest.fixture
def mock_github_instance():
    """Create a mock Github instance."""
    return Mock()


@pytest.fixture
def mock_pull_request():
    """Create a mock PullRequest with an ID."""
    pr = Mock(spec=GitauditPullRequest)
    pr.id = "PR_abc123"
    return pr


# --- Input Model Tests ---


class TestInputModels:
    """Test the Pydantic input models."""

    def test_add_comment_input_model(self):
        """Test AddCommentToPullRequestInput model validation."""
        input_model = AddCommentToPullRequestInput(
            owner="test-owner",
            repo="test-repo",
            number=42,
            body="Test comment",
        )
        assert input_model.owner == "test-owner"
        assert input_model.repo == "test-repo"
        assert input_model.number == 42
        assert input_model.body == "Test comment"

    def test_add_label_input_model(self):
        """Test AddLabelToPullRequestInput model validation."""
        input_model = AddLabelToPullRequestInput(
            owner="test-owner",
            repo="test-repo",
            number=42,
            label_names=["bug", "enhancement"],
        )
        assert input_model.owner == "test-owner"
        assert input_model.repo == "test-repo"
        assert input_model.number == 42
        assert input_model.label_names == ["bug", "enhancement"]

    def test_create_reaction_input_model(self):
        """Test CreateReactionToPullRequestCommentInput model validation."""
        input_model = CreateReactionToPullRequestCommentInput(
            comment_node_id="IC_kwDOABCDE123456789",
            reaction=Reaction.THUMBS_UP,
        )
        assert input_model.comment_node_id == "IC_kwDOABCDE123456789"
        assert input_model.reaction == Reaction.THUMBS_UP

    def test_remove_label_input_model(self):
        """Test RemoveLabelFromPullRequestInput model validation."""
        input_model = RemoveLabelFromPullRequestInput(
            owner="test-owner",
            repo="test-repo",
            number=42,
            label_names=["wontfix"],
        )
        assert input_model.owner == "test-owner"
        assert input_model.repo == "test-repo"
        assert input_model.number == 42
        assert input_model.label_names == ["wontfix"]


# --- Function Tests ---


class TestAddCommentToPullRequest:
    """Test the add_comment_to_pull_request function."""

    def test_add_comment_success(self, mock_github_instance, mock_pull_request):
        """Test successfully adding a comment.

        Verifies that add_comment_to_pull_request correctly fetches the PR,
        adds the comment, and returns the comment URL.
        """
        mock_github_instance.pull_request.return_value = mock_pull_request
        mock_github_instance.add_comment.return_value = "IC_commentNodeId123"
        mock_github_instance.get_comment_url.return_value = (
            "https://github.com/test-owner/test-repo/pull/42#issuecomment-123"
        )

        result = add_comment_to_pull_request(
            owner="test-owner",
            repo="test-repo",
            number=42,
            body="Test comment",
            github=mock_github_instance,
        )

        mock_github_instance.pull_request.assert_called_once_with("test-owner", "test-repo", 42, querydata="id")
        mock_github_instance.add_comment.assert_called_once_with(subject_id="PR_abc123", body="Test comment")
        mock_github_instance.get_comment_url.assert_called_once_with("IC_commentNodeId123")
        assert result == "https://github.com/test-owner/test-repo/pull/42#issuecomment-123"

    def test_add_comment_number_none(self, mock_github_instance):
        """Test error when PR ID is None.

        Verifies that the function raises ValueError when the PR ID
        cannot be retrieved.
        """
        mock_pr = Mock()
        mock_pr.id = None
        mock_github_instance.pull_request.return_value = mock_pr

        with pytest.raises(ValueError, match="Could not get ID for PR #42"):
            add_comment_to_pull_request(
                owner="test-owner",
                repo="test-repo",
                number=42,
                body="Test comment",
                github=mock_github_instance,
            )


class TestCreateReactionToPullRequestComment:
    """Test the create_reaction_to_pull_request_comment function."""

    def test_create_reaction_success(self, mock_github_instance):
        """Test successfully creating a reaction on a comment.

        Verifies that create_reaction_to_pull_request_comment correctly
        creates the reaction and returns the comment URL.
        """
        mock_github_instance.get_comment_url.return_value = (
            "https://github.com/test-owner/test-repo/pull/42#issuecomment-123"
        )

        result = create_reaction_to_pull_request_comment(
            comment_node_id="IC_commentNodeId123",
            reaction=Reaction.THUMBS_UP,
            github=mock_github_instance,
        )

        mock_github_instance.create_reaction.assert_called_once_with(
            subject_id="IC_commentNodeId123", content=Reaction.THUMBS_UP
        )
        mock_github_instance.get_comment_url.assert_called_once_with("IC_commentNodeId123")
        assert result == "https://github.com/test-owner/test-repo/pull/42#issuecomment-123"

    def test_create_reaction_with_heart(self, mock_github_instance):
        """Test creating a heart reaction.

        Verifies that different reaction types work correctly.
        """
        mock_github_instance.get_comment_url.return_value = (
            "https://github.com/test-owner/test-repo/pull/42#issuecomment-456"
        )

        result = create_reaction_to_pull_request_comment(
            comment_node_id="IC_anotherComment",
            reaction=Reaction.HEART,
            github=mock_github_instance,
        )

        mock_github_instance.create_reaction.assert_called_once_with(
            subject_id="IC_anotherComment", content=Reaction.HEART
        )
        assert result == "https://github.com/test-owner/test-repo/pull/42#issuecomment-456"


class TestAddLabelToPullRequest:
    """Test the add_label_to_pull_request function."""

    def test_add_single_label_success(self, mock_github_instance, mock_pull_request):
        """Test successfully adding a single label."""
        mock_github_instance.pull_request.return_value = mock_pull_request
        mock_github_instance.get_label_id.return_value = "LABEL_123"

        result = add_label_to_pull_request(
            owner="test-owner",
            repo="test-repo",
            number=42,
            label_names=["bug"],
            github=mock_github_instance,
        )

        mock_github_instance.get_label_id.assert_called_once_with("test-owner", "test-repo", "bug")
        mock_github_instance.add_label_to_labelable.assert_called_once_with(
            labelable_id="PR_abc123", label_ids=["LABEL_123"]
        )
        assert result == "Successfully added labels [bug] to PR #42 in test-owner/test-repo."

    def test_add_multiple_labels_success(self, mock_github_instance, mock_pull_request):
        """Test successfully adding multiple labels."""
        mock_github_instance.pull_request.return_value = mock_pull_request
        mock_github_instance.get_label_id.side_effect = ["LABEL_1", "LABEL_2"]

        result = add_label_to_pull_request(
            owner="test-owner",
            repo="test-repo",
            number=42,
            label_names=["bug", "enhancement"],
            github=mock_github_instance,
        )

        assert mock_github_instance.get_label_id.call_count == 2
        mock_github_instance.add_label_to_labelable.assert_called_once_with(
            labelable_id="PR_abc123", label_ids=["LABEL_1", "LABEL_2"]
        )
        assert result == "Successfully added labels [bug, enhancement] to PR #42 in test-owner/test-repo."

    def test_add_label_not_found(self, mock_github_instance, mock_pull_request):
        """Test error when label is not found."""
        mock_github_instance.pull_request.return_value = mock_pull_request
        mock_github_instance.get_label_id.return_value = None

        with pytest.raises(ValueError, match="Labels not found in test-owner/test-repo: nonexistent"):
            add_label_to_pull_request(
                owner="test-owner",
                repo="test-repo",
                number=42,
                label_names=["nonexistent"],
                github=mock_github_instance,
            )

    def test_add_label_some_not_found(self, mock_github_instance, mock_pull_request):
        """Test error when some labels are not found."""
        mock_github_instance.pull_request.return_value = mock_pull_request
        mock_github_instance.get_label_id.side_effect = ["LABEL_1", None, None]

        with pytest.raises(ValueError, match="Labels not found in test-owner/test-repo: bad1, bad2"):
            add_label_to_pull_request(
                owner="test-owner",
                repo="test-repo",
                number=42,
                label_names=["bug", "bad1", "bad2"],
                github=mock_github_instance,
            )

    def test_add_label_number_none(self, mock_github_instance):
        """Test error when PR ID is None."""
        mock_pr = Mock()
        mock_pr.id = None
        mock_github_instance.pull_request.return_value = mock_pr

        with pytest.raises(ValueError, match="Could not get ID for PR #42"):
            add_label_to_pull_request(
                owner="test-owner",
                repo="test-repo",
                number=42,
                label_names=["bug"],
                github=mock_github_instance,
            )


class TestRemoveLabelFromPullRequest:
    """Test the remove_label_from_pull_request function."""

    def test_remove_single_label_success(self, mock_github_instance, mock_pull_request):
        """Test successfully removing a single label."""
        mock_github_instance.pull_request.return_value = mock_pull_request
        mock_github_instance.get_label_id.return_value = "LABEL_123"

        result = remove_label_from_pull_request(
            owner="test-owner",
            repo="test-repo",
            number=42,
            label_names=["bug"],
            github=mock_github_instance,
        )

        mock_github_instance.get_label_id.assert_called_once_with("test-owner", "test-repo", "bug")
        mock_github_instance.remove_label_from_labelable.assert_called_once_with(
            labelable_id="PR_abc123", label_ids=["LABEL_123"]
        )
        assert result == "Successfully removed labels [bug] from PR #42 in test-owner/test-repo."

    def test_remove_multiple_labels_success(self, mock_github_instance, mock_pull_request):
        """Test successfully removing multiple labels."""
        mock_github_instance.pull_request.return_value = mock_pull_request
        mock_github_instance.get_label_id.side_effect = ["LABEL_1", "LABEL_2"]

        result = remove_label_from_pull_request(
            owner="test-owner",
            repo="test-repo",
            number=42,
            label_names=["bug", "wontfix"],
            github=mock_github_instance,
        )

        assert mock_github_instance.get_label_id.call_count == 2
        mock_github_instance.remove_label_from_labelable.assert_called_once_with(
            labelable_id="PR_abc123", label_ids=["LABEL_1", "LABEL_2"]
        )
        assert result == "Successfully removed labels [bug, wontfix] from PR #42 in test-owner/test-repo."

    def test_remove_label_not_found(self, mock_github_instance, mock_pull_request):
        """Test error when label is not found."""
        mock_github_instance.pull_request.return_value = mock_pull_request
        mock_github_instance.get_label_id.return_value = None

        with pytest.raises(ValueError, match="Labels not found in test-owner/test-repo: nonexistent"):
            remove_label_from_pull_request(
                owner="test-owner",
                repo="test-repo",
                number=42,
                label_names=["nonexistent"],
                github=mock_github_instance,
            )

    def test_remove_label_number_none(self, mock_github_instance):
        """Test error when PR ID is None."""
        mock_pr = Mock()
        mock_pr.id = None
        mock_github_instance.pull_request.return_value = mock_pr

        with pytest.raises(ValueError, match="Could not get ID for PR #42"):
            remove_label_from_pull_request(
                owner="test-owner",
                repo="test-repo",
                number=42,
                label_names=["bug"],
                github=mock_github_instance,
            )
