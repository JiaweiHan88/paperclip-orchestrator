"""Test cases for the file_content module."""

import json
from unittest.mock import Mock

import pytest

from ai_tools_gerrit.file_content import (
    FileContentInput,
    get_file_content,
)
from ai_tools_gerrit.gerrit_client import GerritApiError


@pytest.fixture
def mock_gerrit() -> Mock:
    return Mock()


# ---------------------------------------------------------------------------
# Input model tests
# ---------------------------------------------------------------------------


class TestFileContentInput:
    def test_defaults(self) -> None:
        m = FileContentInput(project="my/project", file_path="README.md")
        assert m.project == "my/project"
        assert m.file_path == "README.md"
        assert m.branch == "master"
        assert m.max_file_size == 50000

    def test_all_fields(self) -> None:
        m = FileContentInput(project="p", file_path="f.py", branch="main", max_file_size=1000)
        assert m.branch == "main"
        assert m.max_file_size == 1000


# ---------------------------------------------------------------------------
# get_file_content
# ---------------------------------------------------------------------------


class TestGetFileContent:
    def test_successful_retrieval(self, mock_gerrit: Mock) -> None:
        content = "print('hello')\n"
        mock_gerrit.get_raw.return_value = json.dumps(content)
        result = get_file_content(project="my/project", file_path="main.py", gerrit=mock_gerrit)
        assert result == content

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get_raw.return_value = json.dumps("x")
        get_file_content(project="my/project", file_path="src/main.py", gerrit=mock_gerrit)
        call_url = mock_gerrit.get_raw.call_args[0][0]
        assert "my%2Fproject" in call_url
        assert "src%2Fmain.py" in call_url

    def test_custom_branch(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get_raw.return_value = json.dumps("x")
        get_file_content(project="p", file_path="f.py", gerrit=mock_gerrit, branch="develop")
        call_url = mock_gerrit.get_raw.call_args[0][0]
        assert "develop" in call_url

    def test_file_too_large(self, mock_gerrit: Mock) -> None:
        large_content = "x" * 100
        mock_gerrit.get_raw.return_value = json.dumps(large_content)
        result = get_file_content(project="p", file_path="f.py", gerrit=mock_gerrit, max_file_size=50)
        assert "too large" in result
        assert "100" in result
        assert "50" in result

    def test_file_not_found(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get_raw.side_effect = GerritApiError("not found", status_code=404)
        result = get_file_content(project="my/project", file_path="missing.py", gerrit=mock_gerrit)
        assert "not found" in result.lower()
        assert "missing.py" in result

    def test_access_denied(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get_raw.side_effect = GerritApiError("forbidden", status_code=403)
        result = get_file_content(project="p", file_path="f.py", gerrit=mock_gerrit)
        assert "Access denied" in result

    def test_auth_error(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get_raw.side_effect = GerritApiError("unauthorized", status_code=401)
        result = get_file_content(project="p", file_path="f.py", gerrit=mock_gerrit)
        assert "Authentication required" in result

    def test_binary_file(self, mock_gerrit: Mock) -> None:
        # Non-JSON response that can't be parsed
        mock_gerrit.get_raw.return_value = "not valid json {{{"
        result = get_file_content(project="p", file_path="image.png", gerrit=mock_gerrit)
        assert "could not be decoded" in result.lower()

    def test_generic_api_error(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get_raw.side_effect = GerritApiError("server error", status_code=500)
        result = get_file_content(project="p", file_path="f.py", gerrit=mock_gerrit)
        assert "Error fetching file content" in result
