import json
from json import JSONDecodeError

import pytest

from ai_tools_github.github_search import (
    CodeSearchResult,
    GitHubSearch,
    GitHubSearchItem,
    GitHubSearchResponse,
)

ITEM_1 = {
    "name": "example_1.py",
    "path": "src/example_1.py",
    "text_matches": [
        {
            "object_url": "https://cc-github.bmwgroup.net/api/v3/repositories/1/contents/src/example_1.py?ref=12345",
            "object_type": "FileContent",
            "property": "content",
            "fragment": "TODO: fix this",
            "matches": [{"text": "TODO", "indices": [0, 3]}],
        },
        {
            "object_url": "https://cc-github.bmwgroup.net/api/v3/repositories/1/contents/src/example_1.py?ref=abcde",
            "object_type": "FileContent",
            "property": "content",
            "fragment": "TODO: fix this please",
            "matches": [{"text": "TODO", "indices": [0, 3]}],
        },
    ],
}

ITEM_2 = {
    "name": "example_2.py",
    "path": "src/example_2.py",
    "text_matches": [
        {
            "object_url": "https://cc-github.bmwgroup.net/api/v3/repositories/1/contents/src/example_2.py?ref=123456789",
            "object_type": "FileContent",
            "property": "content",
            "fragment": "We have this TODO: we need to fix this",
            "matches": [{"text": "TODO", "indices": [13, 16]}],
        },
        {
            "object_url": "https://cc-github.bmwgroup.net/api/v3/repositories/1/contents/src/example_2.py?ref=abcdefghi",
            "object_type": "FileContent",
            "property": "content",
            "fragment": "Let's create a TODO!",
            "matches": [{"text": "TODO", "indices": [15, 18]}],
        },
    ],
}

RAW_RESPONSE = {
    "total_count": 2,
    "incomplete_results": False,
    "items": [ITEM_1, ITEM_2],
    "some_attribute": "Not relevant",
}

EXPECTED_SEARCH_RESPONSE = GitHubSearchResponse(
    total_count=2,
    incomplete_results=False,
    items=[GitHubSearchItem(**ITEM_1), GitHubSearchItem(**ITEM_2)],
)

EXPECTED_SEARCH_RESULT_1 = CodeSearchResult(
    keyword="TODO",
    file_name="example_1.py",
    file_path="src/example_1.py",
    fragments=["TODO: fix this", "TODO: fix this please"],
)

EXPECTED_SEARCH_RESULT_2 = CodeSearchResult(
    keyword="TODO",
    file_name="example_2.py",
    file_path="src/example_2.py",
    fragments=["We have this TODO: we need to fix this", "Let's create a TODO!"],
)

EXPECTED_MARKDOWN = """
## INFORMATION FROM A GITHUB SEARCH:
Using keyword 'TODO' 2 files containing the keyword were found in the repository 'test-owner/test-repo'.
**file data**:
- file_name: example_1.py
- file_path: src/example_1.py
- context:
['TODO: fix this', 'TODO: fix this please']

**file data**:
- file_name: example_2.py
- file_path: src/example_2.py
- context:
['We have this TODO: we need to fix this', "Let's create a TODO!"]
"""

EXPECTED_MARKDOWN_NO_ENTRIES = ""


@pytest.fixture
def search_tool():
    tool = GitHubSearch(
        github_token="test-token",
        owner="test-owner",
        repo="test-repo",
        keyword="TODO",
    )
    return tool


@pytest.fixture
def mock_github_instance(mocker):
    mock_github_instance = mocker.Mock()
    mocker.patch(
        "ai_tools_github.github_search.get_cc_github_instance",
        return_value=mock_github_instance,
    )
    return mock_github_instance


def test_create_code_search_result(search_tool):
    """
    Test that _create_search_result correctly constructs a CodeSearchResult object.

    This test verifies that the method extracts relevant fields from a GitHub API
    search result entry and populates the CodeSearchResult object as expected.

    """
    search_item_1 = GitHubSearchItem(**ITEM_1)
    search_item_2 = GitHubSearchItem(**ITEM_2)
    search_result_1 = search_tool._create_code_search_result(search_item_1)
    search_result_2 = search_tool._create_code_search_result(search_item_2)
    assert search_result_1 == EXPECTED_SEARCH_RESULT_1
    assert search_result_2 == EXPECTED_SEARCH_RESULT_2


def test_to_markdown(search_tool):
    """
    Test that _to_markdown correctly renders a list of CodeSearchResult objects into Markdown.

    This test ensures that the Jinja2 template renders the expected Markdown output
    when provided with a list of CodeSearchResult objects.

    """
    search_results = [EXPECTED_SEARCH_RESULT_1, EXPECTED_SEARCH_RESULT_2]
    markdown_output = search_tool._to_markdown(search_results)
    assert markdown_output == EXPECTED_MARKDOWN


def test_create_code_search_result_empty_response(mocker, mock_github_instance, search_tool):
    """Test that get_search_data handles empty search results correctly."""
    empty_response = {"total_count": 0, "incomplete_results": False, "items": []}
    mock_github_instance.v3_get.return_value = json.dumps(empty_response)

    mocker.patch("ai_tools_github.github_search.json.loads", return_value=empty_response)

    markdown_output = search_tool.get_search_data()

    assert markdown_output == EXPECTED_MARKDOWN_NO_ENTRIES


def test_JSONDecodeError(mocker, mock_github_instance, search_tool):
    """Test that get_search_data raises JSONDecodeError on invalid JSON."""
    mock_github_instance.v3_get.return_value = "Apparently not a JSON string."
    mocker.patch(
        "ai_tools_github.github_search.json.loads",
        side_effect=JSONDecodeError("Expecting value", "doc", 0),
    )

    with pytest.raises(JSONDecodeError):
        search_tool.get_search_data()


def test_github_api_integration(mocker, mock_github_instance, search_tool):
    """
    Test that the search functionality correctly calls the GitHub API with proper parameters.

    This test verifies:
    - The correct API endpoint is called (/search/code)
    - The correct headers are passed
    - The query parameters are properly formatted
    - The response is processed correctly
    """
    # Setup mock response
    api_response = {
        "total_count": 2,
        "incomplete_results": False,
        "items": [ITEM_1, ITEM_2],
    }
    mock_github_instance.v3_get.return_value = json.dumps(api_response)

    # Call the method
    result = search_tool.get_search_data()

    # Verify the API was called with correct parameters
    mock_github_instance.v3_get.assert_called_once_with(
        url_part="/search/code",
        update_headers={"Accept": "application/vnd.github.text-match+json"},
        params={"q": "TODO repo:test-owner/test-repo"},
    )

    # Verify the result is not empty and contains expected content
    assert result != ""
    assert "TODO" in result
    assert "example_1.py" in result
    assert "example_2.py" in result


def test_query_parameter_construction():
    """
    Test that query parameters are constructed correctly for different inputs.
    """
    # Test basic construction
    tool1 = GitHubSearch(github_token="token", owner="myorg", repo="myrepo", keyword="TODO")
    assert tool1.query_params == {"q": "TODO repo:myorg/myrepo"}

    # Test with special characters in keyword
    tool2 = GitHubSearch(github_token="token", owner="org", repo="repo", keyword="TODO: fix this")
    assert tool2.query_params == {"q": "TODO: fix this repo:org/repo"}

    # Test with different owner/repo
    tool3 = GitHubSearch(github_token="token", owner="facebook", repo="react", keyword="useState")
    assert tool3.query_params == {"q": "useState repo:facebook/react"}


def test_get_cc_github_instance_called_with_token(mocker):
    """
    Test that get_cc_github_instance is called with the correct token.
    """
    mock_get_cc_github = mocker.patch("ai_tools_github.github_search.get_cc_github_instance")
    mock_github_instance = mocker.Mock()
    mock_get_cc_github.return_value = mock_github_instance

    token = "my-secret-token"
    GitHubSearch(github_token=token, owner="owner", repo="repo", keyword="keyword")

    # Verify get_cc_github_instance was called with the correct token
    mock_get_cc_github.assert_called_once_with(token)


def test_api_error_handling(mocker, mock_github_instance, search_tool):
    """
    Test that API errors are properly handled.
    """
    # Test when API call raises an exception
    from requests.exceptions import HTTPError

    mock_github_instance.v3_get.side_effect = HTTPError("404 Not Found")

    with pytest.raises(HTTPError):
        search_tool.get_search_data()


def test_successful_search_flow_integration(mocker):
    """
    Integration test that verifies the entire search flow works correctly.

    This test mocks get_cc_github_instance but verifies the complete flow:
    1. Instance creation
    2. API call with correct parameters
    3. Response parsing
    4. Markdown generation
    """
    # Mock the get_cc_github_instance function
    mock_get_cc_github = mocker.patch("ai_tools_github.github_search.get_cc_github_instance")
    mock_github_instance = mocker.Mock()
    mock_get_cc_github.return_value = mock_github_instance

    # Setup API response
    api_response = {"total_count": 1, "incomplete_results": False, "items": [ITEM_1]}
    mock_github_instance.v3_get.return_value = json.dumps(api_response)

    # Create search tool and execute
    search_tool = GitHubSearch(github_token="test-token", owner="test-owner", repo="test-repo", keyword="TODO")

    result = search_tool.get_search_data()

    # Verify get_cc_github_instance was called with token
    mock_get_cc_github.assert_called_once_with("test-token")

    # Verify API call was made correctly
    mock_github_instance.v3_get.assert_called_once_with(
        url_part="/search/code",
        update_headers={"Accept": "application/vnd.github.text-match+json"},
        params={"q": "TODO repo:test-owner/test-repo"},
    )

    # Verify result contains expected content
    assert "## INFORMATION FROM A GITHUB SEARCH:" in result
    assert "TODO" in result
    assert "example_1.py" in result
