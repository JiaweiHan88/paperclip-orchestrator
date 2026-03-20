from ai_tools_github.issues import GitHubIssueExtractor

mock_raw_issue_data = {
    "repository": {
        "issue": {
            "title": "Test Issue Title",
            "number": 123,
            "url": "https://example.com/owner/repo/issues/123",
            "body": "This is a test issue body with some content.\n"
            "image link 1: https://cc-github.company.net/storage/user/10/files/96e456de-7b78-4119-acfb-6ca170ca948e\n"
            "image link 2: https://cc-github.company.net/storage/user/20/files/ae91249e-b8f9-4f50-89f4-1c7870746100",
            "bodyHTML": "<p>This is a test issue body with some content.</p>"
            '<p>image link 1: <img src="https://cc-github.company.net/storage/user/10/files/96e456de-7b78-4119-acfb-6ca170ca948e?token=AAAHLOFABO1LLRU7AXH4AL3IRXRWQ" alt="image" style="max-width: 100%;">'
            "</a></p>"
            '<p>image link 2: <img src="https://cc-github.company.net/storage/user/20/files/ae91249e-b8f9-4f50-89f4-1c7870746100?token=AAAHLOFABO1LLR12AXHAAA3IRXRWQ" alt="image" style="max-width: 100%;">'
            "</a></p>",
            "labels": {
                "nodes": [
                    {"name": "bug"},
                    {"name": "enhancement"},
                ]
            },
            "comments": {
                "nodes": [
                    {
                        "body": "This is a test comment 0. Please check this @AliceBob. There is also some random URL: https://example.org/example/1",
                        "bodyHTML": "This is a test comment 0. Please check this @AliceBob. There is also some random URL: https://example.org/example/1",
                        "author": {"login": "comment_author_0"},
                        "createdAt": "2023-01-01T12:00:00Z",
                    },
                    {
                        "body": "This is a test comment 1. There is also some other random URL: https://otherexample.org/example/2\nAlso here is another PR: https://github.com/owner/repo/pull/700 "
                        "image link 3: https://cc-github.company.net/storage/user/30/files/961156de-7b78-4119-acfb-6ca170ca948e\n",
                        "bodyHTML": '<img src="https://cc-github.company.net/storage/user/30/files/961156de-7b78-4119-acfb-6ca170ca948e?token=AAAHLABCWABC7AAAOHBEXNDIRTJ4G" alt="image" style="max-width: 100%;">',
                        "author": {"login": "comment_author_1"},
                        "createdAt": "2023-01-02T12:00:00Z",
                    },
                    {
                        "body": "This is a test comment 2. Please check this @AliceBob",
                        "bodyHTML": "This is a test comment 2. Please check this @AliceBob",
                        "author": {"login": "dependabot"},
                        "createdAt": "2023-01-01T12:00:00Z",
                    },
                    {
                        "body": "This is a test comment 3. thank you for your contribution. Please check this @AliceBob",
                        "bodyHTML": "This is a test comment 3. thank you for your contribution. Please check this @AliceBob",
                        "author": {"login": "comment_author_3"},
                        "createdAt": "2023-01-01T12:00:00Z",
                    },
                    {
                        "body": "This is a test comment 4. Please check this @AliceBob",
                        "bodyHTML": "This is a test comment 4. Please check this @AliceBob",
                        "author": {"login": "tu-comment_author_3"},
                        "createdAt": "2023-01-01T12:00:00Z",
                    },
                ]
            },
            "timelineItems": {
                "nodes": [
                    {
                        "__typename": "CrossReferencedEvent",
                        "createdAt": "2023-01-02T12:00:00Z",
                        "source": {
                            "__typename": "PullRequest",
                            "number": 123,
                            "title": "Test Pull Request 0",
                            "url": "https://example.com/owner/repo/pull/123",
                            "merged": True,
                            "author": {"login": "pr_author_0"},
                        },
                    },
                    {
                        "__typename": "CrossReferencedEvent",
                        "createdAt": "2024-01-03T12:00:00Z",
                        "source": {
                            "__typename": "PullRequest",
                            "number": 456,
                            "title": "Test Pull Request 1",
                            "url": "https://example.com/owner/repo/pull/456",
                            "merged": True,
                            "author": {"login": "pr_author_1"},
                        },
                    },
                    {
                        "__typename": "CrossReferencedEvent",
                        "createdAt": "2025-01-01T12:00:00Z",
                        "source": {
                            "__typename": "Issue",
                            "number": 42,
                            "title": "Test Issue 0",
                            "url": "https://example.com/owner/repo/issues/42",
                            "author": {"login": "issue_author"},
                            "body": "I am having this issue.",
                            "labels": {
                                "nodes": [
                                    {"name": "bug"},
                                    {"name": "enhancement"},
                                ]
                            },
                        },
                    },
                    {
                        "__typename": "ReferencedEvent",
                        "createdAt": "2023-01-04T12:00:00Z",
                        "actor": {"login": "actor_1"},
                        "commit": {
                            "message": "Test commit message. Mention @AliceBob."
                            "\nReviewed-by: Alice\n"
                            "Reviewed-by: Bob bob@web.com\n",
                            "oid": "e3a1b2c4d5e6f7890abc1234567890abcdef1234",
                            "committedDate": "2023-01-04T12:00:00Z",
                        },
                    },
                ]
            },
        }
    }
}

expected_markdown_output = """## INFORMATION FROM THE GITHUB ISSUE:

**Issue title:**  
Test Issue Title

**Labels:**
bug
enhancement

**Issue body:**
This is a test issue body with some content.
image link 1: https://cc-github.company.net/storage/user/10/files/96e456de-7b78-4119-acfb-6ca170ca948e
image link 2: https://cc-github.company.net/storage/user/20/files/ae91249e-b8f9-4f50-89f4-1c7870746100

**Comments:**
- Author commented on **2023-01-01 12:00:00+00:00**:
    This is a test comment 0. Please check this @Author. There is also some random URL: https://example.org/example/1
- Author commented on **2023-01-02 12:00:00+00:00**:
    This is a test comment 1. There is also some other random URL: https://otherexample.org/example/2
    Also here is another PR: https://github.com/owner/repo/pull/700 image link 3: https://cc-github.company.net/storage/user/30/files/961156de-7b78-4119-acfb-6ca170ca948e

**Image links:**
- https://cc-github.company.net/storage/user/10/files/96e456de-7b78-4119-acfb-6ca170ca948e?token=AAAHLOFABO1LLRU7AXH4AL3IRXRWQ
- https://cc-github.company.net/storage/user/20/files/ae91249e-b8f9-4f50-89f4-1c7870746100?token=AAAHLOFABO1LLR12AXHAAA3IRXRWQ
- https://cc-github.company.net/storage/user/30/files/961156de-7b78-4119-acfb-6ca170ca948e?token=AAAHLABCWABC7AAAOHBEXNDIRTJ4G

**Linked PRs:**
- #123 - https://example.com/owner/repo/pull/123 - Test Pull Request 0 - (merged)
- #456 - https://example.com/owner/repo/pull/456 - Test Pull Request 1 - (merged)
- #None - https://github.com/owner/repo/pull/700 - None - (merged N/A)

**Grouped Links by Domain:**
- **cc-github.company.net**
    - https://cc-github.company.net/storage/user/10/files/96e456de-7b78-4119-acfb-6ca170ca948e
    - https://cc-github.company.net/storage/user/20/files/ae91249e-b8f9-4f50-89f4-1c7870746100
    - https://cc-github.company.net/storage/user/30/files/961156de-7b78-4119-acfb-6ca170ca948e
- **example.org**
    - https://example.org/example/1
- **otherexample.org**
    - https://otherexample.org/example/2
- **github.com**
    - https://github.com/owner/repo/pull/700

**Referenced Events:**
- **Type**: Commit  
  - **message**: Test commit message. Mention @Author.
  - **oid**: e3a1b2c4d5e6f7890abc1234567890abcdef1234  
  - **Date**: 2023-01-04 12:00:00+00:00

**Cross Referenced Events:**
- **Type**: PullRequest  
  - **Title**: Test Pull Request 0  
  - **URL**: https://example.com/owner/repo/pull/123  
  - **Date**: 2023-01-02 12:00:00+00:00
- **Type**: PullRequest  
  - **Title**: Test Pull Request 1  
  - **URL**: https://example.com/owner/repo/pull/456  
  - **Date**: 2024-01-03 12:00:00+00:00
- **Type**: Issue  
  - **Title**: Test Issue 0  
  - **URL**: https://example.com/owner/repo/issues/42  
  - **Date**: 2025-01-01 12:00:00+00:00"""


def test_structure_and_filter_issue_data(mocker):
    """
    Test the entire logic apart from API calls of the GitHubIssueExtractor tool.
    Using mocked raw response data and an expected markdown output.
    Comparing the expected markdown output with the actual markdown output of the tool.

    Includes filtering out comment 2 (author is dependabot)
    and filtering out comment 3 ('thank you for your contribution').
    Filters out comment 4 (author starts with 'tu-').
    Both comments are filtered out using the filter functions from filter_comments.py
    Besides structuring the data using the pydantic models from local issue models, it
    also includes sanitizing names: replacing real names with 'Author'.

    """
    github_token = "test_github_token"
    owner = "test_owner"
    repo = "test_repo"
    number = 123

    mock_github_class = mocker.patch("ai_tools_github.issues.get_cc_github_instance")

    extractor = GitHubIssueExtractor(github_token, owner, repo, number)

    mock_github_instance = mock_github_class.return_value
    mock_github_instance.query.return_value = mock_raw_issue_data
    md_output = extractor.get_issue_data()

    assert md_output == expected_markdown_output


def test_get_cc_github_instance_called_with_correct_token(mocker):
    """
    Test that get_cc_github_instance is called with the correct token during initialization.
    """
    mock_get_cc_github = mocker.patch("ai_tools_github.issues.get_cc_github_instance")
    mock_github_instance = mocker.Mock()
    mock_get_cc_github.return_value = mock_github_instance

    token = "my-secret-issue-token"

    GitHubIssueExtractor(github_token=token, owner="test-owner", repo="test-repo", number=456)

    # Verify get_cc_github_instance was called with the correct token
    mock_get_cc_github.assert_called_once_with(token)


def test_github_query_method_called_correctly(mocker):
    """
    Test that the GitHub query method is called with correct parameters.

    This verifies:
    - The correct GraphQL query structure is used
    - The query includes necessary issue data fields
    - The owner, repo, and number parameters are embedded in the query string
    """
    mock_get_cc_github = mocker.patch("ai_tools_github.issues.get_cc_github_instance")
    mock_github_instance = mocker.Mock()
    mock_get_cc_github.return_value = mock_github_instance

    # Setup mock response
    mock_github_instance.query.return_value = mock_raw_issue_data

    # Create extractor and run
    extractor = GitHubIssueExtractor(github_token="test-token", owner="test-owner", repo="test-repo", number=789)

    result = extractor.get_issue_data()

    # Verify query was called
    mock_github_instance.query.assert_called_once()

    # Get the actual query that was called
    call_args = mock_github_instance.query.call_args[0]  # positional arguments
    query_string = call_args[0]

    # Verify query contains expected GraphQL structure
    assert "repository" in query_string
    assert "issue" in query_string
    assert "title" in query_string
    assert "body" in query_string
    assert "comments" in query_string
    assert "timelineItems" in query_string

    # Verify the query includes the correct owner, repo, and number
    assert 'owner:"test-owner"' in query_string
    assert 'name:"test-repo"' in query_string
    assert "number:789" in query_string

    # Verify result is returned
    assert result is not None


def test_initialization_parameters_stored_correctly(mocker):
    """
    Test that initialization parameters are stored correctly in the instance.
    """
    mock_get_cc_github = mocker.patch("ai_tools_github.issues.get_cc_github_instance")
    mock_github_instance = mocker.Mock()
    mock_get_cc_github.return_value = mock_github_instance

    extractor = GitHubIssueExtractor(github_token="token-123", owner="my-org", repo="my-repo", number=999)

    # Verify all parameters are stored correctly
    assert extractor.github_token == "token-123"
    assert extractor.owner == "my-org"
    assert extractor.repo == "my-repo"
    assert extractor.number == 999
    assert extractor.github is mock_github_instance


def test_filtering_and_sanitization_integration(mocker):
    """
    Integration test to verify that filtering and sanitization work correctly.

    This test verifies:
    - Unwanted comments are filtered out (dependabot, thank you messages, etc.)
    - Author names are sanitized to @Author
    - The filtering functions are actually applied
    """
    mock_get_cc_github = mocker.patch("ai_tools_github.issues.get_cc_github_instance")
    mock_github_instance = mocker.Mock()
    mock_get_cc_github.return_value = mock_github_instance

    # Use the existing mock data which includes filterable content
    mock_github_instance.query.return_value = mock_raw_issue_data

    extractor = GitHubIssueExtractor(github_token="test-token", owner="test-owner", repo="test-repo", number=123)

    result = extractor.get_issue_data()

    # Verify filtered content is NOT in the result
    # Comment from dependabot should be filtered out
    assert "dependabot" not in result.lower()

    # "thank you for your contribution" comment should be filtered out
    assert "thank you for your contribution" not in result.lower()

    # Author names should be sanitized to @Author
    # The original comments have @AliceBob which should become @Author
    assert "@AliceBob" not in result
    if "@" in result:  # Only check if there are @ mentions
        assert "@Author" in result

    # Verify good content is still present
    assert "Test Issue Title" in result
    assert "This is a test comment 0" in result  # This comment should not be filtered


def test_url_extraction_and_grouping(mocker):
    """
    Test that URL extraction and grouping works correctly.

    This verifies:
    - URLs are extracted from issue body and comments
    - URLs are grouped by domain
    - Different URL patterns are handled correctly
    """
    mock_get_cc_github = mocker.patch("ai_tools_github.issues.get_cc_github_instance")
    mock_github_instance = mocker.Mock()
    mock_get_cc_github.return_value = mock_github_instance

    mock_github_instance.query.return_value = mock_raw_issue_data

    extractor = GitHubIssueExtractor(github_token="test-token", owner="test-owner", repo="test-repo", number=123)

    result = extractor.get_issue_data()

    # Verify that different domains are properly grouped
    assert "cc-github.company.net" in result
    assert "example.org" in result
    assert "otherexample.org" in result
    assert "github.com" in result

    # Verify specific URLs are present
    assert "https://example.org/example/1" in result
    assert "https://otherexample.org/example/2" in result
    assert "https://github.com/owner/repo/pull/700" in result


def test_error_handling_for_api_failures(mocker):
    """
    Test that API failures are properly handled.
    """
    mock_get_cc_github = mocker.patch("ai_tools_github.issues.get_cc_github_instance")
    mock_github_instance = mocker.Mock()
    mock_get_cc_github.return_value = mock_github_instance

    # Simulate API failure
    mock_github_instance.query.side_effect = Exception("API Error")

    extractor = GitHubIssueExtractor(github_token="test-token", owner="test-owner", repo="test-repo", number=123)

    # The method should raise the exception
    try:
        extractor.get_issue_data()
        assert False, "Expected exception was not raised"
    except Exception as e:
        assert "API Error" in str(e)
