"""Tests for the branch module."""

from unittest.mock import Mock

import pytest

from ai_tools_github.branch import (
    CreateBranchInput,
    create_branch,
)


class TestCreateBranchInput:
    """Test the CreateBranchInput model."""

    def test_valid_input(self):
        """Test valid input parameters with all required fields."""
        input_data = CreateBranchInput(
            owner="owner",
            repo="repo",
            branch_name="feature/new-feature",
            base_ref="main",
        )
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.branch_name == "feature/new-feature"
        assert input_data.base_ref == "main"

    def test_with_commit_sha_base(self):
        """Test input with a commit SHA as base reference."""
        input_data = CreateBranchInput(
            owner="software-factory",
            repo="xpad-shared",
            branch_name="bugfix/fix-123",
            base_ref="abc123def456",
        )
        assert input_data.branch_name == "bugfix/fix-123"
        assert input_data.base_ref == "abc123def456"

    def test_with_release_branch(self):
        """Test input for creating a release branch."""
        input_data = CreateBranchInput(
            owner="org",
            repo="project",
            branch_name="release/v1.0.0",
            base_ref="develop",
        )
        assert input_data.branch_name == "release/v1.0.0"
        assert input_data.base_ref == "develop"


class TestCreateBranch:
    """Test the create_branch function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_github = Mock()

    def test_create_branch_success(self):
        """Test successful branch creation.

        Verifies that create_branch correctly resolves the base reference,
        calls the GitHub API to create the branch, and returns a success message.
        """
        mock_commit = Mock()
        mock_commit.oid = "abc123def456789"
        self.mock_github.get_commit_for_expression.return_value = mock_commit

        result = create_branch(
            owner="test-owner",
            repo="test-repo",
            branch_name="feature/new-feature",
            base_ref="main",
            github=self.mock_github,
        )

        self.mock_github.get_commit_for_expression.assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            expression="main",
            querydata="oid",
        )
        self.mock_github.create_branch.assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            base_oid="abc123def456789",
            ref_name="feature/new-feature",
        )
        assert "Successfully created branch 'feature/new-feature'" in result
        assert "test-owner/test-repo" in result
        assert "abc123de" in result  # First 8 chars of OID

    def test_create_branch_from_commit_sha(self):
        """Test branch creation from a specific commit SHA.

        Verifies that a branch can be created using a commit SHA as the base reference.
        """
        mock_commit = Mock()
        mock_commit.oid = "deadbeef12345678"
        self.mock_github.get_commit_for_expression.return_value = mock_commit

        result = create_branch(
            owner="owner",
            repo="repo",
            branch_name="hotfix/urgent-fix",
            base_ref="deadbeef12345678",
            github=self.mock_github,
        )

        self.mock_github.get_commit_for_expression.assert_called_once_with(
            owner="owner",
            repo="repo",
            expression="deadbeef12345678",
            querydata="oid",
        )
        assert "Successfully created branch 'hotfix/urgent-fix'" in result
        assert "deadbeef" in result

    def test_create_branch_base_ref_not_found(self):
        """Test error handling when base reference cannot be resolved.

        Verifies that an appropriate error message is returned when the
        base reference doesn't exist or cannot be resolved to a commit.
        """
        mock_commit = Mock()
        mock_commit.oid = None
        self.mock_github.get_commit_for_expression.return_value = mock_commit

        result = create_branch(
            owner="owner",
            repo="repo",
            branch_name="feature/test",
            base_ref="nonexistent-branch",
            github=self.mock_github,
        )

        assert "Error" in result
        assert "nonexistent-branch" in result
        self.mock_github.create_branch.assert_not_called()

    def test_create_branch_from_tag(self):
        """Test branch creation from a tag reference.

        Verifies that a branch can be created from a tag.
        """
        mock_commit = Mock()
        mock_commit.oid = "tag123commit456"
        self.mock_github.get_commit_for_expression.return_value = mock_commit

        result = create_branch(
            owner="org",
            repo="project",
            branch_name="release/v2.0.0",
            base_ref="v1.5.0",
            github=self.mock_github,
        )

        self.mock_github.get_commit_for_expression.assert_called_once_with(
            owner="org",
            repo="project",
            expression="v1.5.0",
            querydata="oid",
        )
        assert "Successfully created branch 'release/v2.0.0'" in result
        assert "based on 'v1.5.0'" in result

    def test_create_branch_with_special_characters(self):
        """Test branch creation with special characters in name.

        Verifies that branches with slashes and other special characters
        are handled correctly.
        """
        mock_commit = Mock()
        mock_commit.oid = "special123chars456"
        self.mock_github.get_commit_for_expression.return_value = mock_commit

        result = create_branch(
            owner="my-org",
            repo="my-project",
            branch_name="feature/JIRA-123/add-login",
            base_ref="develop",
            github=self.mock_github,
        )

        self.mock_github.create_branch.assert_called_once_with(
            owner="my-org",
            repo="my-project",
            base_oid="special123chars456",
            ref_name="feature/JIRA-123/add-login",
        )
        assert "feature/JIRA-123/add-login" in result
