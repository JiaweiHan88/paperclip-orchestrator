"""Tests for the commit_on_branch module."""

from unittest.mock import Mock, call

import pytest

from ai_tools_github.commit_on_branch import (
    CreateCommitOnBranchInput,
    FileAdditionInput,
    FileDeletionInput,
    create_commit_on_branch,
)


class TestFileAdditionInput:
    """Test the FileAdditionInput model."""

    def test_valid_file_addition(self):
        """Test valid file addition input."""
        addition = FileAdditionInput(
            path="src/main.py",
            content="print('Hello, World!')",
        )
        assert addition.path == "src/main.py"
        assert addition.content == "print('Hello, World!')"

    def test_file_addition_with_multiline_content(self):
        """Test file addition with multiline content."""
        content = """# My Module

def hello():
    return "Hello"
"""
        addition = FileAdditionInput(
            path="module.py",
            content=content,
        )
        assert addition.path == "module.py"
        assert "def hello():" in addition.content


class TestFileDeletionInput:
    """Test the FileDeletionInput model."""

    def test_valid_file_deletion(self):
        """Test valid file deletion input."""
        deletion = FileDeletionInput(path="old_file.py")
        assert deletion.path == "old_file.py"

    def test_file_deletion_with_nested_path(self):
        """Test file deletion with nested path."""
        deletion = FileDeletionInput(path="deprecated/old/config.json")
        assert deletion.path == "deprecated/old/config.json"


class TestCreateCommitOnBranchInput:
    """Test the CreateCommitOnBranchInput model."""

    def test_minimal_input(self):
        """Test input with only required fields."""
        input_data = CreateCommitOnBranchInput(
            owner="owner",
            repo="repo",
            branch_name="main",
            message_headline="Fix bug",
        )
        assert input_data.owner == "owner"
        assert input_data.repo == "repo"
        assert input_data.branch_name == "main"
        assert input_data.message_headline == "Fix bug"
        assert input_data.message_body is None
        assert input_data.additions is None
        assert input_data.deletions is None

    def test_full_input(self):
        """Test input with all fields populated."""
        additions = [FileAdditionInput(path="file.py", content="content")]
        deletions = [FileDeletionInput(path="old.py")]

        input_data = CreateCommitOnBranchInput(
            owner="org",
            repo="project",
            branch_name="feature/branch",
            message_headline="Add feature",
            message_body="Detailed description of the feature.",
            additions=additions,
            deletions=deletions,
        )
        assert input_data.owner == "org"
        assert input_data.repo == "project"
        assert input_data.branch_name == "feature/branch"
        assert input_data.message_headline == "Add feature"
        assert input_data.message_body == "Detailed description of the feature."
        assert input_data.additions is not None
        assert input_data.deletions is not None
        assert len(input_data.additions) == 1
        assert len(input_data.deletions) == 1


class TestCreateCommitOnBranch:
    """Test the create_commit_on_branch function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_github = Mock()

    def test_create_commit_success(self):
        """Test successful commit creation with file additions.

        Verifies that create_commit_on_branch correctly gets the HEAD SHA,
        creates the commit, and returns a success message.
        """
        mock_head_commit = Mock()
        mock_head_commit.oid = "head123sha456"
        self.mock_github.get_commit_for_expression.return_value = mock_head_commit

        mock_result_commit = Mock()
        mock_result_commit.oid = "new123commit456"
        mock_result_commit.message_headline = "Add new file"
        self.mock_github.create_commit_on_branch.return_value = mock_result_commit

        additions = [FileAdditionInput(path="src/new_file.py", content="print('Hello')")]

        result = create_commit_on_branch(
            owner="test-owner",
            repo="test-repo",
            branch_name="feature/add-file",
            message_headline="Add new file",
            github=self.mock_github,
            additions=additions,
        )

        self.mock_github.get_commit_for_expression.assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            expression="feature/add-file",
            querydata="oid",
        )
        assert "Successfully created commit" in result
        assert "new123commit456" in result
        assert "Add new file" in result

    def test_create_commit_with_body(self):
        """Test commit creation with message body.

        Verifies that the message body is passed correctly to the API.
        """
        mock_head_commit = Mock()
        mock_head_commit.oid = "head123"
        self.mock_github.get_commit_for_expression.return_value = mock_head_commit

        mock_result = Mock()
        mock_result.oid = "result123"
        mock_result.message_headline = "Update documentation"
        self.mock_github.create_commit_on_branch.return_value = mock_result

        additions = [FileAdditionInput(path="README.md", content="# Updated Readme")]

        result = create_commit_on_branch(
            owner="owner",
            repo="repo",
            branch_name="main",
            message_headline="Update documentation",
            message_body="This updates the README with new instructions.",
            github=self.mock_github,
            additions=additions,
        )

        # Verify message_body was passed
        call_kwargs = self.mock_github.create_commit_on_branch.call_args[1]
        assert call_kwargs["message_body"] == "This updates the README with new instructions."
        assert "Successfully created commit" in result

    def test_create_commit_with_deletions(self):
        """Test commit creation with file deletions.

        Verifies that file deletions are properly converted and passed to the API.
        """
        mock_head_commit = Mock()
        mock_head_commit.oid = "head789"
        self.mock_github.get_commit_for_expression.return_value = mock_head_commit

        mock_result = Mock()
        mock_result.oid = "delete123"
        mock_result.message_headline = "Remove deprecated files"
        self.mock_github.create_commit_on_branch.return_value = mock_result

        deletions = [
            FileDeletionInput(path="old_file.py"),
            FileDeletionInput(path="deprecated/config.json"),
        ]

        result = create_commit_on_branch(
            owner="owner",
            repo="repo",
            branch_name="cleanup",
            message_headline="Remove deprecated files",
            github=self.mock_github,
            deletions=deletions,
        )

        call_kwargs = self.mock_github.create_commit_on_branch.call_args[1]
        assert len(call_kwargs["deletions"]) == 2
        assert "Successfully created commit" in result

    def test_create_commit_with_additions_and_deletions(self):
        """Test commit creation with both additions and deletions.

        Verifies that a commit can include both file additions and deletions.
        """
        mock_head_commit = Mock()
        mock_head_commit.oid = "headmixed123"
        self.mock_github.get_commit_for_expression.return_value = mock_head_commit

        mock_result = Mock()
        mock_result.oid = "mixed456"
        mock_result.message_headline = "Refactor code"
        self.mock_github.create_commit_on_branch.return_value = mock_result

        additions = [FileAdditionInput(path="new_module.py", content="# New module")]
        deletions = [FileDeletionInput(path="old_module.py")]

        result = create_commit_on_branch(
            owner="owner",
            repo="repo",
            branch_name="refactor",
            message_headline="Refactor code",
            github=self.mock_github,
            additions=additions,
            deletions=deletions,
        )

        call_kwargs = self.mock_github.create_commit_on_branch.call_args[1]
        assert len(call_kwargs["additions"]) == 1
        assert len(call_kwargs["deletions"]) == 1
        assert "Successfully created commit" in result

    def test_create_commit_branch_not_found(self):
        """Test error handling when branch cannot be resolved.

        Verifies that an appropriate error message is returned when the
        branch doesn't exist.
        """
        mock_commit = Mock()
        mock_commit.oid = None
        self.mock_github.get_commit_for_expression.return_value = mock_commit

        additions = [FileAdditionInput(path="test.txt", content="content")]
        result = create_commit_on_branch(
            owner="owner",
            repo="repo",
            branch_name="nonexistent-branch",
            message_headline="Test commit",
            github=self.mock_github,
            additions=additions,
        )

        assert "Error" in result
        assert "nonexistent-branch" in result
        self.mock_github.create_commit_on_branch.assert_not_called()

    def test_create_commit_no_return_value(self):
        """Test commit creation when API returns None.

        Verifies that a fallback message is returned when the API
        doesn't return commit details.
        """
        mock_head_commit = Mock()
        mock_head_commit.oid = "head123"
        self.mock_github.get_commit_for_expression.return_value = mock_head_commit
        self.mock_github.create_commit_on_branch.return_value = None

        additions = [FileAdditionInput(path="test.txt", content="content")]
        result = create_commit_on_branch(
            owner="owner",
            repo="repo",
            branch_name="main",
            message_headline="Quick fix",
            github=self.mock_github,
            additions=additions,
        )

        assert "Commit created on branch 'main'" in result
        assert "owner/repo" in result

    def test_create_commit_empty_additions_and_deletions(self):
        """Test commit creation with empty additions and deletions lists.

        Verifies that a ValueError is raised when no file changes are provided.
        """
        with pytest.raises(ValueError) as exc_info:
            create_commit_on_branch(
                owner="owner",
                repo="repo",
                branch_name="test",
                message_headline="Empty commit",
                github=self.mock_github,
                additions=[],
                deletions=[],
            )

        assert "Cannot create a commit without any file changes" in str(exc_info.value)
        self.mock_github.create_commit_on_branch.assert_not_called()
