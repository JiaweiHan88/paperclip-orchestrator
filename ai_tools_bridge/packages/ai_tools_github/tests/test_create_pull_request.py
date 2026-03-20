"""Tests for the create_pull_request module."""

from unittest.mock import Mock

import pytest

from ai_tools_github.create_pull_request import (
    CreatePullRequestInput,
    create_pull_request,
)
from ai_tools_github.models.pull_request import PULL_REQUEST_GRAPHQL_QUERY


class TestCreatePullRequestInput:
    """Test the CreatePullRequestInput model."""

    def test_minimal_input(self):
        """Test input with only required fields."""
        input_data = CreatePullRequestInput(
            owner="owner",
            repo="repo",
            head_ref_name="feature/branch",
            base_ref_name="main",
            title="Add new feature",
        )
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.head_ref_name == "feature/branch"
        assert input_data.base_ref_name == "main"
        assert input_data.title == "Add new feature"
        assert input_data.body is None
        assert input_data.draft is False

    def test_full_input(self):
        """Test input with all fields populated."""
        input_data = CreatePullRequestInput(
            owner="software-factory",
            repo="xpad-shared",
            head_ref_name="feature/new-feature",
            base_ref_name="develop",
            title="Implement feature X",
            body="## Summary\nThis PR adds feature X.",
            draft=True,
        )
        assert input_data.owner == "software-factory"
        assert input_data.repo == "xpad-shared"
        assert input_data.head_ref_name == "feature/new-feature"
        assert input_data.base_ref_name == "develop"
        assert input_data.title == "Implement feature X"
        assert input_data.body == "## Summary\nThis PR adds feature X."
        assert input_data.draft is True

    def test_cross_repo_pr(self):
        """Test input for cross-repository pull request."""
        input_data = CreatePullRequestInput(
            owner="upstream-org",
            repo="project",
            head_ref_name="fork-owner:feature-branch",
            base_ref_name="main",
            title="Contribution from fork",
        )
        assert input_data.head_ref_name == "fork-owner:feature-branch"


class TestCreatePullRequest:
    """Test the create_pull_request function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_github = Mock()

    def test_create_pull_request_success(self):
        """Test successful pull request creation.

        Verifies that create_pull_request correctly gets the repository ID,
        creates the PR, and returns formatted markdown.
        """
        mock_repo = Mock()
        mock_repo.id = "repo123"
        self.mock_github.get_repository.return_value = mock_repo

        mock_pr = Mock()
        mock_pr.url = "https://github.com/owner/repo/pull/42"
        self.mock_github.create_pull_request.return_value = mock_pr

        result = create_pull_request(
            owner="owner",
            repo="repo",
            head_ref_name="feature/branch",
            base_ref_name="main",
            title="Add new feature",
            github=self.mock_github,
        )

        self.mock_github.get_repository.assert_called_once_with("owner", "repo", "id")
        self.mock_github.create_pull_request.assert_called_once_with(
            repository_id="repo123",
            head_ref_name="feature/branch",
            base_ref_name="main",
            title="Add new feature",
            body=None,
            draft=False,
            querydata="url",
        )
        # The result should contain some PR info (will be processed by pull_request_to_markdown)
        assert result is not None

    def test_create_pull_request_with_body(self):
        """Test PR creation with description body.

        Verifies that the body is passed correctly to the API.
        """
        mock_repo = Mock()
        mock_repo.id = "repo456"
        self.mock_github.get_repository.return_value = mock_repo
        self.mock_github.create_pull_request.return_value = None

        result = create_pull_request(
            owner="owner",
            repo="repo",
            head_ref_name="bugfix/fix-123",
            base_ref_name="main",
            title="Fix bug #123",
            body="This PR fixes the bug described in issue #123.",
            github=self.mock_github,
        )

        self.mock_github.create_pull_request.assert_called_once()
        call_kwargs = self.mock_github.create_pull_request.call_args[1]
        assert call_kwargs["body"] == "This PR fixes the bug described in issue #123."
        # Fallback message when PR returns None
        assert "Pull request created" in result
        assert "Fix bug #123" in result

    def test_create_pull_request_as_draft(self):
        """Test PR creation as draft.

        Verifies that the draft flag is passed correctly.
        """
        mock_repo = Mock()
        mock_repo.id = "repo789"
        self.mock_github.get_repository.return_value = mock_repo
        self.mock_github.create_pull_request.return_value = None

        result = create_pull_request(
            owner="owner",
            repo="repo",
            head_ref_name="wip/experimental",
            base_ref_name="develop",
            title="WIP: Experimental feature",
            draft=True,
            github=self.mock_github,
        )

        call_kwargs = self.mock_github.create_pull_request.call_args[1]
        assert call_kwargs["draft"] is True

    def test_create_pull_request_repo_not_found(self):
        """Test error handling when repository ID cannot be obtained.

        Verifies that an appropriate error message is returned when the
        repository doesn't exist or cannot be accessed.
        """
        mock_repo = Mock()
        mock_repo.id = None
        self.mock_github.get_repository.return_value = mock_repo

        result = create_pull_request(
            owner="owner",
            repo="nonexistent-repo",
            head_ref_name="feature/test",
            base_ref_name="main",
            title="Test PR",
            github=self.mock_github,
        )

        assert "Error" in result
        assert "owner/nonexistent-repo" in result
        self.mock_github.create_pull_request.assert_not_called()

    def test_create_pull_request_fallback_message(self):
        """Test fallback message when PR creation returns None.

        Verifies that a fallback message is generated when the API
        doesn't return PR details.
        """
        mock_repo = Mock()
        mock_repo.id = "repoid"
        self.mock_github.get_repository.return_value = mock_repo
        self.mock_github.create_pull_request.return_value = None

        result = create_pull_request(
            owner="test-owner",
            repo="test-repo",
            head_ref_name="feature/my-feature",
            base_ref_name="main",
            title="My Feature",
            github=self.mock_github,
        )

        assert "Pull request created in test-owner/test-repo" in result
        assert "**Title:** My Feature" in result
        assert "feature/my-feature" in result
        assert "main" in result
