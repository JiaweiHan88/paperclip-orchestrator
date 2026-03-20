"""Tests for the code_search module."""

from __future__ import annotations

import json
from unittest.mock import Mock

import pytest

from ai_tools_github.code_search import (
    CodeSearchInput,
    _build_query,
    _format_results,
    search_code,
)


# ---------------------------------------------------------------------------
# Input model validation
# ---------------------------------------------------------------------------


class TestCodeSearchInput:
    """Tests for CodeSearchInput pydantic model."""

    def test_query_only(self):
        inp = CodeSearchInput(query="import torch")
        assert inp.query == "import torch"
        assert inp.owner is None
        assert inp.repo is None
        assert inp.per_page == 30

    def test_query_with_owner_and_repo(self):
        inp = CodeSearchInput(query="TODO", owner="software-factory", repo="ai-tools-lib")
        assert inp.owner == "software-factory"
        assert inp.repo == "ai-tools-lib"

    def test_query_with_owner_only(self):
        inp = CodeSearchInput(query="TODO", owner="software-factory")
        assert inp.owner == "software-factory"
        assert inp.repo is None

    def test_repo_without_owner_raises(self):
        with pytest.raises(ValueError, match="requires 'owner'"):
            CodeSearchInput(query="TODO", repo="ai-tools-lib")

    def test_per_page_min(self):
        with pytest.raises(Exception):
            CodeSearchInput(query="x", per_page=0)

    def test_per_page_max(self):
        with pytest.raises(Exception):
            CodeSearchInput(query="x", per_page=101)

    def test_custom_per_page(self):
        inp = CodeSearchInput(query="x", per_page=50)
        assert inp.per_page == 50


# ---------------------------------------------------------------------------
# Query builder
# ---------------------------------------------------------------------------


class TestBuildQuery:
    """Tests for _build_query helper."""

    def test_query_only(self):
        assert _build_query("TODO", None, None) == "TODO"

    def test_with_owner_and_repo(self):
        assert _build_query("TODO", "swh", "repo1") == "TODO repo:swh/repo1"

    def test_with_owner_only(self):
        assert _build_query("TODO", "swh", None) == "TODO org:swh"

    def test_complex_query(self):
        q = _build_query("import torch language:python", "my-org", None)
        assert q == "import torch language:python org:my-org"


# ---------------------------------------------------------------------------
# Result formatter
# ---------------------------------------------------------------------------

SAMPLE_API_RESPONSE = {
    "total_count": 2,
    "incomplete_results": False,
    "items": [
        {
            "name": "main.py",
            "path": "src/main.py",
            "html_url": "https://github.com/owner/repo/blob/main/src/main.py",
            "repository": {"full_name": "owner/repo"},
            "text_matches": [
                {"fragment": "import torch\nimport torch.nn as nn"},
            ],
        },
        {
            "name": "utils.py",
            "path": "lib/utils.py",
            "html_url": "https://github.com/owner/repo/blob/main/lib/utils.py",
            "repository": {"full_name": "owner/repo"},
            "text_matches": [
                {"fragment": "import torch.optim"},
            ],
        },
    ],
}


class TestFormatResults:
    """Tests for _format_results helper."""

    def test_empty_items(self):
        result = _format_results("foo", {"total_count": 0, "items": []})
        assert "No code results found" in result

    def test_missing_items_key(self):
        result = _format_results("foo", {"total_count": 0})
        assert "No code results found" in result

    def test_basic_formatting(self):
        md = _format_results("import torch", SAMPLE_API_RESPONSE)
        assert "## Code Search Results" in md
        assert "**2** result(s)" in md
        assert "owner/repo: src/main.py" in md
        assert "owner/repo: lib/utils.py" in md
        assert "import torch" in md

    def test_fragments_present(self):
        md = _format_results("import torch", SAMPLE_API_RESPONSE)
        assert "import torch.nn as nn" in md
        assert "import torch.optim" in md

    def test_no_text_matches(self):
        data = {
            "total_count": 1,
            "items": [
                {
                    "name": "a.py",
                    "path": "a.py",
                    "html_url": "https://example.com/a.py",
                    "repository": {"full_name": "org/repo"},
                    "text_matches": [],
                }
            ],
        }
        md = _format_results("x", data)
        assert "org/repo: a.py" in md
        # No code blocks expected
        assert "```" not in md


# ---------------------------------------------------------------------------
# search_code function
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_github():
    return Mock()


class TestSearchCode:
    """Tests for the search_code function."""

    def test_successful_search(self, mock_github):
        mock_github.v3_get.return_value = json.dumps(SAMPLE_API_RESPONSE)

        result = search_code(query="import torch", github=mock_github, owner="owner", repo="repo")

        mock_github.v3_get.assert_called_once()
        call_args = mock_github.v3_get.call_args
        assert call_args[0][0] == "/search/code"
        assert "import torch repo:owner/repo" in call_args[1]["params"]["q"]
        assert "## Code Search Results" in result

    def test_search_no_scope(self, mock_github):
        mock_github.v3_get.return_value = json.dumps(SAMPLE_API_RESPONSE)

        search_code(query="TODO", github=mock_github)

        call_args = mock_github.v3_get.call_args
        assert call_args[1]["params"]["q"] == "TODO"

    def test_search_org_scope(self, mock_github):
        mock_github.v3_get.return_value = json.dumps(SAMPLE_API_RESPONSE)

        search_code(query="TODO", github=mock_github, owner="my-org")

        call_args = mock_github.v3_get.call_args
        assert call_args[1]["params"]["q"] == "TODO org:my-org"

    def test_empty_results(self, mock_github):
        mock_github.v3_get.return_value = json.dumps({"total_count": 0, "items": []})

        result = search_code(query="nonexistent_xyz", github=mock_github)

        assert "No code results found" in result

    def test_json_decode_error(self, mock_github):
        mock_github.v3_get.return_value = "not valid json {"

        result = search_code(query="q", github=mock_github)

        assert "Error" in result

    def test_api_422_error(self, mock_github):
        mock_github.v3_get.side_effect = Exception("422 Unprocessable Entity")

        result = search_code(query="x", github=mock_github)

        assert "422" in result or "rejected" in result

    def test_api_403_error(self, mock_github):
        mock_github.v3_get.side_effect = Exception("403 Forbidden")

        result = search_code(query="x", github=mock_github)

        assert "rate limit" in result or "denied" in result

    def test_generic_error(self, mock_github):
        mock_github.v3_get.side_effect = Exception("connection timeout")

        result = search_code(query="x", github=mock_github)

        assert "connection timeout" in result

    def test_per_page_parameter(self, mock_github):
        mock_github.v3_get.return_value = json.dumps({"total_count": 0, "items": []})

        search_code(query="TODO", github=mock_github, per_page=10)

        call_args = mock_github.v3_get.call_args
        assert call_args[1]["params"]["per_page"] == "10"

    def test_text_match_header_sent(self, mock_github):
        mock_github.v3_get.return_value = json.dumps({"total_count": 0, "items": []})

        search_code(query="q", github=mock_github)

        call_args = mock_github.v3_get.call_args
        assert "application/vnd.github.text-match+json" in call_args[1]["update_headers"]["Accept"]
