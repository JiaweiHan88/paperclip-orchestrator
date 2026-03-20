"""Test cases for the project_branches module."""

from unittest.mock import Mock

import pytest

from ai_tools_gerrit.project_branches import (
    GetProjectBranchesInput,
    get_project_branches,
)


@pytest.fixture
def mock_gerrit() -> Mock:
    return Mock()


# ---------------------------------------------------------------------------
# Input model tests
# ---------------------------------------------------------------------------


class TestGetProjectBranchesInput:
    def test_defaults(self) -> None:
        m = GetProjectBranchesInput(project="my/project")
        assert m.project == "my/project"
        assert m.limit == 50
        assert m.filter_regex is None

    def test_all_fields(self) -> None:
        m = GetProjectBranchesInput(project="p", limit=10, filter_regex="release.*")
        assert m.limit == 10
        assert m.filter_regex == "release.*"


# ---------------------------------------------------------------------------
# get_project_branches
# ---------------------------------------------------------------------------


class TestGetProjectBranches:
    def test_successful_listing(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"ref": "refs/heads/main", "revision": "abc12345def67890"},
            {"ref": "refs/heads/develop", "revision": "1234567890abcdef"},
        ]
        result = get_project_branches(project="my/project", gerrit=mock_gerrit)
        assert "main" in result
        assert "develop" in result
        assert "abc12345" in result
        assert "2 branches" in result

    def test_strips_refs_heads_prefix(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"ref": "refs/heads/feature/foo", "revision": "aabbccdd11223344"},
        ]
        result = get_project_branches(project="p", gerrit=mock_gerrit)
        assert "feature/foo" in result
        assert "refs/heads/" not in result

    def test_head_ref_preserved(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"ref": "HEAD", "revision": "aabbccdd11223344"},
        ]
        result = get_project_branches(project="p", gerrit=mock_gerrit)
        assert "HEAD" in result

    def test_empty_result(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        result = get_project_branches(project="empty-project", gerrit=mock_gerrit)
        assert "No branches found" in result

    def test_with_filter_regex(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"ref": "refs/heads/release/1.0", "revision": "aabbccdd11223344"},
        ]
        get_project_branches(project="p", gerrit=mock_gerrit, filter_regex="release.*")
        call_args = mock_gerrit.get.call_args
        params = call_args[1].get("params") or call_args[0][1] if len(call_args[0]) > 1 else call_args[1]["params"]
        assert params["r"] == "release.*"

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        get_project_branches(project="my/project", gerrit=mock_gerrit)
        call_url = mock_gerrit.get.call_args[0][0]
        assert "my%2Fproject" in call_url

    def test_short_sha_display(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = [
            {"ref": "refs/heads/main", "revision": "abcdef1234567890abcdef"},
        ]
        result = get_project_branches(project="p", gerrit=mock_gerrit)
        assert "abcdef12" in result
        # Full SHA should not appear
        assert "abcdef1234567890abcdef" not in result

    def test_limit_param_passed(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.return_value = []
        get_project_branches(project="p", gerrit=mock_gerrit, limit=10)
        call_args = mock_gerrit.get.call_args
        params = call_args[1].get("params") or call_args[0][1] if len(call_args[0]) > 1 else call_args[1]["params"]
        assert params["n"] == "10"
