"""Test cases for the files module."""

import json
from unittest.mock import Mock

import pytest

from ai_tools_gerrit.files import (
    GetChangeDiffInput,
    GetFileDiffInput,
    ListChangeFilesInput,
    get_change_diff,
    get_file_diff,
    list_change_files,
)
from ai_tools_gerrit.gerrit_client import GerritApiError


@pytest.fixture
def mock_gerrit() -> Mock:
    return Mock()


# ---------------------------------------------------------------------------
# Input model tests
# ---------------------------------------------------------------------------


class TestListChangeFilesInput:
    def test_required_change_id(self) -> None:
        m = ListChangeFilesInput(change_id="12345")
        assert m.change_id == "12345"


class TestGetFileDiffInput:
    def test_required_fields(self) -> None:
        m = GetFileDiffInput(change_id="12345", file_path="src/main.py")
        assert m.change_id == "12345"
        assert m.file_path == "src/main.py"


# ---------------------------------------------------------------------------
# list_change_files
# ---------------------------------------------------------------------------


class TestListChangeFiles:
    def test_shows_file_paths(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {
                "/COMMIT_MSG": {"status": "A", "lines_inserted": 11, "size_delta": 566, "size": 566},
                "src/main.py": {
                    "old_mode": 33188,
                    "new_mode": 33188,
                    "lines_inserted": 10,
                    "lines_deleted": 2,
                    "size_delta": 100,
                    "size": 500,
                },
            },
            {"current_revision_number": 3},
        ]
        result = list_change_files(change_id="12345", gerrit=mock_gerrit)
        assert "src/main.py" in result

    def test_skips_commit_msg(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {
                "/COMMIT_MSG": {"status": "A", "lines_inserted": 8, "size_delta": 400, "size": 400},
                "README.md": {"old_mode": 33188, "new_mode": 33188, "lines_inserted": 1, "lines_deleted": 1},
            },
            {"current_revision_number": 1},
        ]
        result = list_change_files(change_id="12345", gerrit=mock_gerrit)
        assert "/COMMIT_MSG" not in result

    def test_shows_line_counts(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {
                "foo.py": {
                    "old_mode": 33188,
                    "new_mode": 33188,
                    "lines_inserted": 5,
                    "lines_deleted": 3,
                    "size_delta": 20,
                    "size": 100,
                }
            },
            {"current_revision_number": 2},
        ]
        result = list_change_files(change_id="12345", gerrit=mock_gerrit)
        assert "+5" in result
        assert "-3" in result

    def test_status_added_prefix(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {"new_file.py": {"status": "A", "lines_inserted": 20, "size_delta": 500, "size": 500}},
            {"current_revision_number": 1},
        ]
        result = list_change_files(change_id="12345", gerrit=mock_gerrit)
        assert "[A]" in result

    def test_status_deleted_prefix(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {"old_file.py": {"status": "D", "old_mode": 33188, "lines_deleted": 10, "size_delta": -244, "size": 0}},
            {"current_revision_number": 1},
        ]
        result = list_change_files(change_id="12345", gerrit=mock_gerrit)
        assert "[D]" in result

    def test_status_renamed_prefix(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {"moved.py": {"status": "R", "old_mode": 33188, "new_mode": 33188}},
            {"current_revision_number": 1},
        ]
        result = list_change_files(change_id="12345", gerrit=mock_gerrit)
        assert "[R]" in result

    def test_modified_uses_m_prefix(self, mock_gerrit: Mock) -> None:
        """Modified files have no 'status' field in the real Gerrit API."""
        mock_gerrit.get.side_effect = [
            {
                "mod.py": {
                    "old_mode": 33188,
                    "new_mode": 33188,
                    "lines_inserted": 1,
                    "lines_deleted": 1,
                    "size_delta": 0,
                    "size": 200,
                }
            },
            {"current_revision_number": 1},
        ]
        result = list_change_files(change_id="12345", gerrit=mock_gerrit)
        assert "[M]" in result

    def test_shows_patch_set_number(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {"foo.py": {"old_mode": 33188, "new_mode": 33188, "lines_inserted": 1}},
            {"current_revision_number": 4},
        ]
        result = list_change_files(change_id="12345", gerrit=mock_gerrit)
        assert "4" in result

    def test_includes_change_id_in_header(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {"bar.py": {"old_mode": 33188, "new_mode": 33188}},
            {"current_revision_number": 1},
        ]
        result = list_change_files(change_id="99999", gerrit=mock_gerrit)
        assert "99999" in result

    def test_shows_aggregate_totals(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {
                "a.py": {"lines_inserted": 10, "lines_deleted": 2},
                "b.py": {"lines_inserted": 5, "lines_deleted": 3},
            },
            {"current_revision_number": 1},
        ]
        result = list_change_files(change_id="1", gerrit=mock_gerrit)
        assert "Total: 2 files, +15, -5" in result

    def test_shows_old_path_for_renames(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {"new_name.py": {"status": "R", "old_path": "old_name.py"}},
            {"current_revision_number": 1},
        ]
        result = list_change_files(change_id="1", gerrit=mock_gerrit)
        assert "[R]" in result
        assert "renamed from old_name.py" in result


# ---------------------------------------------------------------------------
# get_file_diff
# ---------------------------------------------------------------------------


class TestGetFileDiff:
    def test_decodes_base64_response(self, mock_gerrit: Mock) -> None:
        patch_text = "--- a/foo.py\n+++ b/foo.py\n@@ -1 +1 @@\n-old\n+new\n"
        mock_gerrit.get_raw.return_value = json.dumps(patch_text)
        result = get_file_diff(change_id="12345", file_path="foo.py", gerrit=mock_gerrit)
        assert result == patch_text

    def test_non_string_response_returns_str(self, mock_gerrit: Mock) -> None:
        # If get_raw returns something that isn't a JSON string, return as-is
        mock_gerrit.get_raw.return_value = "plain text diff"
        result = get_file_diff(change_id="12345", file_path="foo.py", gerrit=mock_gerrit)
        assert isinstance(result, str)

    def test_calls_correct_endpoint(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get_raw.return_value = json.dumps("diff")
        get_file_diff(change_id="12345", file_path="src/main.py", gerrit=mock_gerrit)
        call_url = mock_gerrit.get_raw.call_args[0][0]
        assert "12345" in call_url
        assert "src%2Fmain.py" in call_url or "src/main.py" in call_url

    def test_url_encodes_file_path(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get_raw.return_value = json.dumps("diff")
        get_file_diff(change_id="1", file_path="path/to/my file.py", gerrit=mock_gerrit)
        call_url = mock_gerrit.get_raw.call_args[0][0]
        # Space should be percent-encoded
        assert " " not in call_url


# ---------------------------------------------------------------------------
# get_change_diff
# ---------------------------------------------------------------------------


class TestGetChangeDiffInput:
    def test_defaults(self) -> None:
        m = GetChangeDiffInput(change_id="12345")
        assert m.revision_id == "current"
        assert m.file_scope is None

    def test_all_fields(self) -> None:
        m = GetChangeDiffInput(change_id="1", revision_id="2", file_scope=[".py"])
        assert m.file_scope == [".py"]


class TestGetChangeDiff:
    def test_returns_diffs_for_all_files(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            # files listing
            {"src/main.py": {"lines_inserted": 5, "lines_deleted": 2}},
            # diff for src/main.py
            {"content": [{"a": ["old line"], "b": ["new line"]}]},
        ]
        result = get_change_diff(change_id="1", gerrit=mock_gerrit)
        assert "--- a/src/main.py" in result
        assert "+++ b/src/main.py" in result
        assert "-old line" in result
        assert "+new line" in result

    def test_skips_commit_msg(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {"/COMMIT_MSG": {"lines_inserted": 5}, "real.py": {"lines_inserted": 1}},
            {"content": [{"b": ["added"]}]},
        ]
        result = get_change_diff(change_id="1", gerrit=mock_gerrit)
        assert "/COMMIT_MSG" not in result
        assert "real.py" in result

    def test_file_scope_filters_by_extension(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {"main.py": {"lines_inserted": 5}, "style.css": {"lines_inserted": 3}},
            {"content": [{"b": ["code"]}]},
        ]
        result = get_change_diff(change_id="1", gerrit=mock_gerrit, file_scope=[".py"])
        assert "main.py" in result
        assert "style.css" not in result

    def test_graceful_fallback_on_diff_error(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {"fail.py": {"status": "A", "lines_inserted": 10, "lines_deleted": 0}},
            GerritApiError("diff failed", status_code=500),
        ]
        result = get_change_diff(change_id="1", gerrit=mock_gerrit)
        assert "fail.py" in result
        assert "added" in result
        assert "+10" in result

    def test_empty_result_with_scope(self, mock_gerrit: Mock) -> None:
        mock_gerrit.get.side_effect = [
            {"style.css": {"lines_inserted": 3}},
        ]
        result = get_change_diff(change_id="1", gerrit=mock_gerrit, file_scope=[".py"])
        assert "No relevant changes found" in result

    def test_context_lines_truncated(self, mock_gerrit: Mock) -> None:
        long_context = [f"line {i}" for i in range(20)]
        mock_gerrit.get.side_effect = [
            {"main.py": {"lines_inserted": 1}},
            {"content": [{"ab": long_context}]},
        ]
        result = get_change_diff(change_id="1", gerrit=mock_gerrit)
        assert "lines omitted" in result
