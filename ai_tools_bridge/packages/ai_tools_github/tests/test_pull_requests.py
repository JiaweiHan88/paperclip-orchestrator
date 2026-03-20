"""Test cases for pull_requests module."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from ai_tools_github.models.pull_request import (
    Author,
    CheckRun,
    Commit,
    Comment,
    Label,
    MergeCommit,
    PullRequest,
    Repository,
    Review,
    ReviewRequest,
    StatusCheckRollup,
    StatusContext,
    Team,
    User,
    pull_request_list_to_markdown,
    pull_request_to_markdown,
)
from ai_tools_github.pull_requests import (
    PullRequestInput,
    SearchPullRequestsInput,
    get_pull_request,
    inject_to_pull_request_description,
    search_pull_requests,
)


@pytest.fixture
def mock_github_instance():
    """Create a mock Github instance."""
    return Mock()


@pytest.fixture
def sample_author():
    """Create a sample Author object."""
    return Author(login="testuser", typename="Author")


@pytest.fixture
def sample_repository():
    """Create a sample Repository object."""
    return Repository(name="test-repo", name_with_owner="test-owner/test-repo", typename="Repository")


@pytest.fixture
def sample_merge_commit():
    """Create a sample MergeCommit object."""
    return MergeCommit(oid="abc123", committed_date=datetime(2025, 11, 1, 12, 0, 0), typename="MergeCommit")


@pytest.fixture
def sample_pull_request(sample_author, sample_repository, sample_merge_commit):
    """Create a sample PullRequest object."""
    return PullRequest(
        number=42,
        title="Fix bug in authentication",
        body="This PR fixes a critical bug in the authentication module.",
        base_ref_name="main",
        head_ref_name="fix/auth-bug",
        head_ref_oid="abc123def456",
        url="https://github.com/test-owner/test-repo/pull/42",
        id="PR_1234567890",
        closed=False,
        merged=False,
        is_draft=False,
        mergeable="MERGEABLE",
        merge_commit=None,
        review_decision="APPROVED",
        additions=50,
        deletions=20,
        reviews=[],
        labels=[Label(name="bug", color="red", typename="Label")],
        participants=[],
        author=sample_author,
        repository=sample_repository,
        comments=[],
        commits=[],
        typename="PullRequest",
    )


@pytest.fixture
def sample_merged_pull_request(sample_author, sample_repository, sample_merge_commit):
    """Create a sample merged PullRequest object."""
    return PullRequest(
        number=100,
        title="Add new feature",
        body="This PR adds a new feature.",
        base_ref_name="main",
        head_ref_name="feature/new-thing",
        head_ref_oid="def456ghi789",
        url="https://github.com/test-owner/test-repo/pull/100",
        id="PR_9876543210",
        closed=True,
        merged=True,
        is_draft=False,
        mergeable="UNKNOWN",
        merge_commit=sample_merge_commit,
        review_decision="APPROVED",
        additions=150,
        deletions=30,
        reviews=[],
        labels=[Label(name="enhancement", color="blue", typename="Label")],
        participants=[],
        author=sample_author,
        repository=sample_repository,
        comments=[],
        commits=[],
        typename="PullRequest",
    )


@pytest.fixture
def sample_closed_pull_request(sample_author, sample_repository):
    """Create a sample closed (not merged) PullRequest object."""
    return PullRequest(
        number=99,
        title="Closed without merge",
        body="This PR was closed without merging.",
        base_ref_name="main",
        head_ref_name="feature/abandoned",
        head_ref_oid="ghi789jkl012",
        url="https://github.com/test-owner/test-repo/pull/99",
        id="PR_1111111111",
        closed=True,
        merged=False,
        is_draft=False,
        mergeable="UNKNOWN",
        merge_commit=None,
        review_decision="CHANGES_REQUESTED",
        additions=10,
        deletions=5,
        reviews=[],
        labels=[],
        participants=[],
        author=sample_author,
        repository=sample_repository,
        comments=[],
        commits=[],
        typename="PullRequest",
    )


@pytest.fixture
def sample_review(sample_author):
    """Create a sample Review object."""
    return Review(
        author=sample_author,
        state="APPROVED",
        created_at=datetime(2025, 11, 20, 10, 0, 0),
        body="Looks good to me!",
        id="REV_123",
        typename="Review",
    )


@pytest.fixture
def sample_user():
    """Create a sample User object."""
    return User(login="reviewer1", typename="User")


@pytest.fixture
def sample_team():
    """Create a sample Team object."""
    return Team(name="core-team", typename="Team")


@pytest.fixture
def sample_review_request_user(sample_user):
    """Create a sample ReviewRequest with a user reviewer."""
    return ReviewRequest(
        as_code_owner=False,
        requested_reviewer=sample_user,
        typename="Review",
    )


@pytest.fixture
def sample_review_request_team(sample_team):
    """Create a sample ReviewRequest with a team reviewer."""
    return ReviewRequest(
        as_code_owner=True,
        requested_reviewer=sample_team,
        typename="Review",
    )


@pytest.fixture
def sample_check_run():
    """Create a sample CheckRun object."""
    return CheckRun(
        name="CI Tests",
        status="COMPLETED",
        conclusion="SUCCESS",
        summary="All tests passed",
        completed_at=datetime(2025, 11, 1, 12, 0, 0),
        typename="CheckRun",
    )


@pytest.fixture
def sample_status_context():
    """Create a sample StatusContext object."""
    return StatusContext(
        context="continuous-integration/jenkins",
        state="SUCCESS",
        typename="StatusContext",
    )


@pytest.fixture
def sample_status_check_rollup(sample_check_run, sample_status_context):
    """Create a sample StatusCheckRollup object."""
    return StatusCheckRollup(
        contexts=[sample_check_run, sample_status_context],
        typename="StatusCheckRollup",
    )


@pytest.fixture
def sample_commit(sample_status_check_rollup):
    """Create a sample Commit object."""
    return Commit(
        message_headline="Fix bug in authentication",
        message_body="Detailed commit message",
        oid="abc123def456",
        status_check_rollup=sample_status_check_rollup,
        typename="Commit",
    )


class TestGetPullRequest:
    """Tests for get_pull_request function."""

    def test_get_pull_request_success(self, mock_github_instance, sample_pull_request):
        """Test successful retrieval of a pull request."""
        # Setup mock
        mock_github_instance.pull_request.return_value = sample_pull_request

        # Call function
        result = get_pull_request(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=mock_github_instance,
        )

        # Verify github.pull_request was called with correct parameters
        mock_github_instance.pull_request.assert_called_once()
        call_kwargs = mock_github_instance.pull_request.call_args[1]
        assert call_kwargs["owner"] == "test-owner"
        assert call_kwargs["repo"] == "test-repo"
        assert call_kwargs["number"] == 42
        assert "number" in call_kwargs["querydata"]
        assert "title" in call_kwargs["querydata"]

        # Verify result is markdown string
        assert isinstance(result, str)
        assert "Fix bug in authentication" in result
        assert "test-owner/test-repo#42" in result
        assert "main <- fix/auth-bug" in result

    def test_get_pull_request_with_merged_pr(self, mock_github_instance, sample_merged_pull_request):
        """Test retrieval of a merged pull request."""
        mock_github_instance.pull_request.return_value = sample_merged_pull_request

        result = get_pull_request(
            owner="test-owner",
            repo="test-repo",
            number=100,
            github=mock_github_instance,
        )

        # Verify merged status is reflected in markdown
        assert "merged" in result.lower()
        assert "abc123" in result
        assert "test-owner/test-repo#100" in result

    def test_get_pull_request_with_closed_pr(self, mock_github_instance, sample_closed_pull_request):
        """Test retrieval of a closed (not merged) pull request."""
        mock_github_instance.pull_request.return_value = sample_closed_pull_request

        result = get_pull_request(
            owner="test-owner",
            repo="test-repo",
            number=99,
            github=mock_github_instance,
        )

        # Verify closed status is reflected in markdown
        assert "closed" in result.lower()
        assert "test-owner/test-repo#99" in result

    def test_get_pull_request_with_comments(self, mock_github_instance, sample_pull_request, sample_author):
        """Test pull request with comments."""
        sample_pull_request.comments = [
            Comment(
                author=sample_author,
                body="This looks good!",
                created_at=datetime(2025, 11, 2, 10, 0, 0),
                typename="Comment",
            ),
            Comment(
                author=Author(login="reviewer2", typename="Author"),
                body="Please add tests.",
                created_at=datetime(2025, 11, 2, 11, 0, 0),
                typename="Comment",
            ),
        ]

        mock_github_instance.pull_request.return_value = sample_pull_request

        result = get_pull_request(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=mock_github_instance,
        )

        # Verify comments are in output
        assert "Comments:" in result
        assert "This looks good!" in result
        assert "Please add tests." in result
        assert "testuser:" in result
        assert "reviewer2:" in result

    def test_get_pull_request_with_labels(self, mock_github_instance, sample_pull_request):
        """Test pull request with multiple labels."""
        sample_pull_request.labels = [
            Label(name="bug", color="red", typename="Label"),
            Label(name="urgent", color="orange", typename="Label"),
            Label(name="security", color="yellow", typename="Label"),
        ]

        mock_github_instance.pull_request.return_value = sample_pull_request

        result = get_pull_request(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=mock_github_instance,
        )

        # Verify labels are in output
        assert "Labels:" in result
        assert "bug" in result
        assert "urgent" in result
        assert "security" in result

    def test_get_pull_request_api_error(self, mock_github_instance):
        """Test handling of API errors."""
        mock_github_instance.pull_request.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            get_pull_request(
                owner="test-owner",
                repo="test-repo",
                number=42,
                github=mock_github_instance,
            )


class TestSearchPullRequests:
    """Tests for search_pull_requests function."""

    def test_search_pull_requests_success(self, mock_github_instance, sample_pull_request):
        """Test successful search for pull requests."""
        mock_github_instance.search_pull_requests.return_value = [sample_pull_request]

        result = search_pull_requests(
            query="repo:test-owner/test-repo is:pr is:open",
            github=mock_github_instance,
        )

        # Verify search was called with correct parameters
        mock_github_instance.search_pull_requests.assert_called_once()
        call_kwargs = mock_github_instance.search_pull_requests.call_args[1]
        assert call_kwargs["search_query"] == "repo:test-owner/test-repo is:pr is:open"
        assert "number" in call_kwargs["querydata"]

        # Verify result is markdown string
        assert isinstance(result, str)
        assert "test-owner/test-repo#42" in result
        assert "Fix bug in authentication" in result

    def test_search_pull_requests_multiple_results(
        self, mock_github_instance, sample_pull_request, sample_merged_pull_request
    ):
        """Test search returning multiple pull requests."""
        mock_github_instance.search_pull_requests.return_value = [
            sample_pull_request,
            sample_merged_pull_request,
        ]

        result = search_pull_requests(
            query="repo:test-owner/test-repo is:pr",
            github=mock_github_instance,
        )

        # Verify both PRs are in result
        assert "test-owner/test-repo#42" in result
        assert "Fix bug in authentication" in result
        assert "test-owner/test-repo#100" in result
        assert "Add new feature" in result

    def test_search_pull_requests_empty_results(self, mock_github_instance):
        """Test search with no results."""
        mock_github_instance.search_pull_requests.return_value = []

        result = search_pull_requests(
            query="repo:test-owner/test-repo is:pr label:nonexistent",
            github=mock_github_instance,
        )

        # Verify empty result
        assert isinstance(result, str)
        assert result == ""

    def test_search_pull_requests_complex_query(self, mock_github_instance, sample_pull_request):
        """Test search with complex query."""
        mock_github_instance.search_pull_requests.return_value = [sample_pull_request]

        complex_query = "repo:software-factory/repo1 is:pr is:open author:testuser label:bug"
        result = search_pull_requests(
            query=complex_query,
            github=mock_github_instance,
        )

        # Verify query was passed correctly
        call_kwargs = mock_github_instance.search_pull_requests.call_args[1]
        assert call_kwargs["search_query"] == complex_query
        assert isinstance(result, str)

    def test_search_pull_requests_api_error(self, mock_github_instance):
        """Test handling of API errors during search."""
        mock_github_instance.search_pull_requests.side_effect = Exception("Search API Error")

        with pytest.raises(Exception, match="Search API Error"):
            search_pull_requests(
                query="repo:test-owner/test-repo is:pr",
                github=mock_github_instance,
            )


class TestPullRequestInput:
    """Tests for PullRequestInput model."""

    def test_pull_request_input_valid(self):
        """Test valid PullRequestInput creation."""
        input_model = PullRequestInput(owner="test-owner", repo="test-repo", number=42)

        assert input_model.owner == "test-owner"
        assert input_model.repo == "test-repo"
        assert input_model.number == 42

    def test_pull_request_input_validation(self):
        """Test validation of PullRequestInput."""
        # Test with example values
        input_model = PullRequestInput(owner="swh", repo="xpad-shared", number=134)

        assert input_model.owner == "swh"
        assert input_model.repo == "xpad-shared"
        assert input_model.number == 134


class TestSearchPullRequestsInput:
    """Tests for SearchPullRequestsInput model."""

    def test_search_pull_request_input_valid(self):
        """Test valid SearchPullRequestsInput creation."""
        input_model = SearchPullRequestsInput(query="repo:test-owner/test-repo is:pr is:open")

        assert input_model.query == "repo:test-owner/test-repo is:pr is:open"

    def test_search_pull_request_input_with_example_queries(self):
        """Test SearchPullRequestsInput with example queries."""
        # Test first example
        input1 = SearchPullRequestsInput(query="repo:software-factory/repo1 is:pr is:open author:someuser")
        assert "software-factory/repo1" in input1.query

        # Test second example
        input2 = SearchPullRequestsInput(query="repo:swh/repo2 is:pr is:closed label:bug")
        assert "swh/repo2" in input2.query
        assert "label:bug" in input2.query


class TestPullRequestToMarkdown:
    """Tests for pull_request_to_markdown helper function."""

    def test_open_pr_markdown(self, sample_pull_request):
        """Test markdown generation for open pull request."""
        result = pull_request_to_markdown(sample_pull_request)

        assert "# [test-owner/test-repo#42]" in result
        assert "Fix bug in authentication" in result
        assert "Open approved mergeable" in result
        assert "main <- fix/auth-bug" in result
        assert "Labels: bug" in result

    def test_open_pr_without_review_decision(self, sample_pull_request):
        """Ensure markdown handles missing review decision."""
        sample_pull_request.review_decision = None

        result = pull_request_to_markdown(sample_pull_request)

        assert "Open unreviewed mergeable" in result

    def test_merged_pr_markdown(self, sample_merged_pull_request):
        """Test markdown generation for merged pull request."""
        result = pull_request_to_markdown(sample_merged_pull_request)

        assert "# [test-owner/test-repo#100]" in result
        assert "Add new feature" in result
        assert "Merged (abc123)" in result
        assert "Labels: enhancement" in result

    def test_closed_pr_markdown(self, sample_closed_pull_request):
        """Test markdown generation for closed pull request."""
        result = pull_request_to_markdown(sample_closed_pull_request)

        assert "# [test-owner/test-repo#99]" in result
        assert "Closed without merge" in result
        assert "Closed" in result

    def test_pr_with_reviews(self, sample_pull_request, sample_review):
        """Test markdown generation for pull request with reviews."""
        sample_pull_request.reviews = [sample_review]

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Reviews:" in result
        assert "testuser" in result
        assert "APPROVED" in result
        assert "Looks good to me!" in result

    def test_pr_with_multiple_reviews(self, sample_pull_request, sample_author):
        """Test markdown generation for pull request with multiple reviews."""
        review1 = Review(
            author=sample_author,
            state="APPROVED",
            created_at=datetime(2025, 11, 20, 10, 0, 0),
            body="LGTM",
            id="REV_1",
            typename="Review",
        )
        review2 = Review(
            author=Author(login="reviewer2", typename="Author"),
            state="CHANGES_REQUESTED",
            created_at=datetime(2025, 11, 20, 11, 0, 0),
            body="Please fix the formatting",
            id="REV_2",
            typename="Review",
        )
        sample_pull_request.reviews = [review1, review2]

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Reviews:" in result
        assert "testuser" in result
        assert "APPROVED" in result
        assert "reviewer2" in result
        assert "CHANGES_REQUESTED" in result
        assert "Please fix the formatting" in result

    def test_pr_without_reviews(self, sample_pull_request):
        """Test markdown generation for pull request without reviews."""
        sample_pull_request.reviews = []

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Reviews:" in result
        assert "No reviews" in result
        assert "Review Decision: APPROVED" in result

    def test_pr_with_user_review_request(self, sample_pull_request, sample_review_request_user):
        """Test markdown generation for pull request with user review request."""
        sample_pull_request.review_requests = [sample_review_request_user]

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Requested Reviews:" in result
        assert "reviewer1" in result
        assert "Code Owner" not in result

    def test_pr_with_team_review_request(self, sample_pull_request, sample_review_request_team):
        """Test markdown generation for pull request with team review request."""
        sample_pull_request.review_requests = [sample_review_request_team]

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Requested Reviews:" in result
        assert "core-team" in result
        assert "(Code Owner)" in result

    def test_pr_with_multiple_review_requests(
        self, sample_pull_request, sample_review_request_user, sample_review_request_team
    ):
        """Test markdown generation for pull request with multiple review requests."""
        sample_pull_request.review_requests = [sample_review_request_user, sample_review_request_team]

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Requested Reviews:" in result
        assert "reviewer1" in result
        assert "core-team" in result
        assert "(Code Owner)" in result

    def test_pr_without_review_requests(self, sample_pull_request):
        """Test markdown generation for pull request without review requests."""
        sample_pull_request.review_requests = []

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Requested Reviews:" in result
        assert "No review requests" in result

    def test_pr_with_none_reviewer_in_review_requests(self, sample_pull_request):
        """Test markdown generation for pull request with None reviewer in review requests."""
        review_request_with_none = ReviewRequest(
            as_code_owner=False,
            requested_reviewer=None,
            typename="Review",
        )
        sample_pull_request.review_requests = [review_request_with_none]

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Requested Reviews:" in result
        assert "No review requests" in result

    def test_pr_with_status_checks(self, sample_pull_request, sample_commit):
        """Test markdown generation for pull request with status checks."""
        sample_pull_request.commits = [sample_commit]

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Status Checks:" in result
        assert "CI Tests" in result
        assert "COMPLETED" in result
        assert "SUCCESS" in result
        assert "continuous-integration/jenkins" in result

    def test_pr_with_check_run_without_conclusion(self, sample_pull_request):
        """Test markdown generation for pull request with check run without conclusion."""
        check_run = CheckRun(
            name="Build",
            status="IN_PROGRESS",
            conclusion=None,
            summary="Building...",
            completed_at=None,
            typename="CheckRun",
        )
        status_check_rollup = StatusCheckRollup(
            contexts=[check_run],
            typename="StatusCheckRollup",
        )
        commit = Commit(
            message_headline="Test commit",
            message_body="",
            oid="abc123",
            status_check_rollup=status_check_rollup,
            typename="Commit",
        )
        sample_pull_request.commits = [commit]

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Status Checks:" in result
        assert "Build" in result
        assert "IN_PROGRESS" in result

    def test_pr_without_status_checks(self, sample_pull_request):
        """Test markdown generation for pull request without status checks."""
        commit = Commit(
            message_headline="Test commit",
            message_body="",
            oid="abc123",
            status_check_rollup=None,
            typename="Commit",
        )
        sample_pull_request.commits = [commit]

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Status Checks:" in result
        assert "No CI checks" in result

    def test_pr_without_commits(self, sample_pull_request):
        """Test markdown generation for pull request without commits."""
        sample_pull_request.commits = []

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Status Checks:" in result
        assert "No CI checks" in result

    def test_pr_with_empty_status_check_contexts(self, sample_pull_request):
        """Test markdown generation for pull request with empty status check contexts."""
        status_check_rollup = StatusCheckRollup(
            contexts=[],
            typename="StatusCheckRollup",
        )
        commit = Commit(
            message_headline="Test commit",
            message_body="",
            oid="abc123",
            status_check_rollup=status_check_rollup,
            typename="Commit",
        )
        sample_pull_request.commits = [commit]

        result = pull_request_to_markdown(sample_pull_request)

        assert "## Status Checks:" in result
        assert "No CI checks" in result


class TestPullRequestListToMarkdown:
    """Tests for pull_request_list_to_markdown helper function."""

    def test_single_pr_list_markdown(self, sample_pull_request):
        """Test markdown generation for single pull request list."""
        result = pull_request_list_to_markdown([sample_pull_request])

        assert "- [test-owner/test-repo#42] Fix bug in authentication" in result

    def test_multiple_pr_list_markdown(
        self, sample_pull_request, sample_merged_pull_request, sample_closed_pull_request
    ):
        """Test markdown generation for multiple pull requests list."""
        result = pull_request_list_to_markdown(
            [
                sample_pull_request,
                sample_merged_pull_request,
                sample_closed_pull_request,
            ]
        )

        assert "- [test-owner/test-repo#42] Fix bug in authentication" in result
        assert "- [test-owner/test-repo#100] Add new feature" in result
        assert "- [test-owner/test-repo#99] Closed without merge" in result
        # Check they're on separate lines
        lines = result.split("\n")
        assert len(lines) == 3

    def test_empty_pr_list_markdown(self):
        """Test markdown generation for empty pull request list."""
        result = pull_request_list_to_markdown([])

        assert result == ""


class TestInjectToPullRequestDescription:
    """Tests for inject_to_pull_request_description function."""

    def test_inject_new_section_to_existing_description(self, mock_github_instance):
        """Test injecting a new section into an existing PR description.

        When the PR description has content but no injection markers,
        the function should append the collapsible section with a
        separator line.

        Mocks:
            - Github instance to verify update_pull_request call
        """
        pr_node_id = "PR_kwDOABCDE123456789"
        injection_title = "Summary"
        start_keyword = "<!-- summary-start -->"
        end_keyword = "<!-- summary-end -->"
        description_old = "This PR implements new feature X."
        injection_text = "This is the summary content."

        inject_to_pull_request_description(
            pr_node_id=pr_node_id,
            injection_title=injection_title,
            start_keyword=start_keyword,
            end_keyword=end_keyword,
            description_old=description_old,
            injection_text=injection_text,
            github=mock_github_instance,
        )

        # Verify the update was called with correct body
        mock_github_instance.update_pull_request.assert_called_once()
        call_args = mock_github_instance.update_pull_request.call_args
        assert call_args[1]["pull_request_id"] == pr_node_id

        body = call_args[1]["body"]
        assert description_old in body
        assert start_keyword in body
        assert end_keyword in body
        assert f"<summary>{injection_title}</summary>" in body
        assert injection_text in body
        assert "---" in body  # Separator
        assert "<details>" in body
        assert "</details>" in body

    def test_inject_updates_existing_section(self, mock_github_instance):
        """Test updating an existing injected section.

        When the PR description already contains the injection markers,
        the function should replace the content between them with the
        new collapsible section.

        Mocks:
            - Github instance to verify update_pull_request call
        """
        pr_node_id = "PR_kwDOABCDE123456789"
        injection_title = "Analysis Results"
        start_keyword = "<!-- analysis-start -->"
        end_keyword = "<!-- analysis-end -->"
        description_old = (
            "This PR fixes a bug.\n\n"
            f"{start_keyword}\n"
            "<details>\n"
            "<summary>Old Analysis</summary>\n\n"
            "Old analysis content.\n\n"
            "</details>\n"
            f"{end_keyword}\n\n"
            "More description here."
        )
        injection_text = "Updated analysis content."

        inject_to_pull_request_description(
            pr_node_id=pr_node_id,
            injection_title=injection_title,
            start_keyword=start_keyword,
            end_keyword=end_keyword,
            description_old=description_old,
            injection_text=injection_text,
            github=mock_github_instance,
        )

        # Verify the update was called
        mock_github_instance.update_pull_request.assert_called_once()
        call_args = mock_github_instance.update_pull_request.call_args
        body = call_args[1]["body"]

        # Should preserve content before and after the injection section
        assert "This PR fixes a bug." in body
        assert "More description here." in body

        # Should contain the new content, not the old
        assert injection_text in body
        assert "Old analysis content" not in body
        assert f"<summary>{injection_title}</summary>" in body

    def test_inject_to_empty_description(self, mock_github_instance):
        """Test injecting into an empty PR description.

        When the PR description is empty or whitespace-only,
        the function should create a new description with just
        the separator and collapsible section.

        Mocks:
            - Github instance to verify update_pull_request call
        """
        pr_node_id = "PR_kwDOABCDE123456789"
        injection_title = "Summary"
        start_keyword = "<!-- summary-start -->"
        end_keyword = "<!-- summary-end -->"
        description_old = ""
        injection_text = "Auto-generated summary."

        inject_to_pull_request_description(
            pr_node_id=pr_node_id,
            injection_title=injection_title,
            start_keyword=start_keyword,
            end_keyword=end_keyword,
            description_old=description_old,
            injection_text=injection_text,
            github=mock_github_instance,
        )

        # Verify the update was called
        mock_github_instance.update_pull_request.assert_called_once()
        call_args = mock_github_instance.update_pull_request.call_args
        body = call_args[1]["body"]

        # Should start with separator
        assert body.startswith("---")
        assert injection_text in body
        assert start_keyword in body
        assert end_keyword in body
        assert f"<summary>{injection_title}</summary>" in body

    def test_inject_with_whitespace_only_description(self, mock_github_instance):
        """Test injecting into a whitespace-only PR description.

        When the PR description contains only whitespace,
        it should be treated as empty and create a new
        description with separator and collapsible section.

        Mocks:
            - Github instance to verify update_pull_request call
        """
        pr_node_id = "PR_kwDOABCDE123456789"
        injection_title = "Summary"
        start_keyword = "<!-- summary-start -->"
        end_keyword = "<!-- summary-end -->"
        description_old = "   \n\n   \t  "
        injection_text = "Auto-generated summary."

        inject_to_pull_request_description(
            pr_node_id=pr_node_id,
            injection_title=injection_title,
            start_keyword=start_keyword,
            end_keyword=end_keyword,
            description_old=description_old,
            injection_text=injection_text,
            github=mock_github_instance,
        )

        # Verify the update was called
        mock_github_instance.update_pull_request.assert_called_once()
        call_args = mock_github_instance.update_pull_request.call_args
        body = call_args[1]["body"]

        # Should start with separator (empty after strip)
        assert body.startswith("---")

    def test_inject_with_start_keyword_only(self, mock_github_instance):
        """Test handling when only start keyword exists.

        When the description contains the start keyword but not
        the end keyword, the function should replace from the
        start keyword to the end of the description.

        Mocks:
            - Github instance to verify update_pull_request call
        """
        pr_node_id = "PR_kwDOABCDE123456789"
        injection_title = "Summary"
        start_keyword = "<!-- summary-start -->"
        end_keyword = "<!-- summary-end -->"
        description_old = f"This PR does something.\n\n{start_keyword}\nSome incomplete section that was never closed."
        injection_text = "New summary content."

        inject_to_pull_request_description(
            pr_node_id=pr_node_id,
            injection_title=injection_title,
            start_keyword=start_keyword,
            end_keyword=end_keyword,
            description_old=description_old,
            injection_text=injection_text,
            github=mock_github_instance,
        )

        # Verify the update was called
        mock_github_instance.update_pull_request.assert_called_once()
        call_args = mock_github_instance.update_pull_request.call_args
        body = call_args[1]["body"]

        # Should preserve content before start keyword
        assert "This PR does something." in body

        # Should have new content
        assert injection_text in body
        assert end_keyword in body

        # Old incomplete content should be gone
        assert "Some incomplete section" not in body

    def test_inject_preserves_content_order(self, mock_github_instance):
        """Test that content order is preserved correctly.

        When injecting into a description with content before and
        after the injection markers, the function should preserve
        the exact order and position of all content.

        Mocks:
            - Github instance to verify update_pull_request call
        """
        pr_node_id = "PR_kwDOABCDE123456789"
        injection_title = "Summary"
        start_keyword = "<!-- summary-start -->"
        end_keyword = "<!-- summary-end -->"
        description_old = (
            "# PR Title\n\n"
            "Description line 1.\n\n"
            "Description line 2.\n\n"
            f"{start_keyword}\n"
            "Old summary\n"
            f"{end_keyword}\n\n"
            "## Testing\n\n"
            "Test instructions here."
        )
        injection_text = "New summary"

        inject_to_pull_request_description(
            pr_node_id=pr_node_id,
            injection_title=injection_title,
            start_keyword=start_keyword,
            end_keyword=end_keyword,
            description_old=description_old,
            injection_text=injection_text,
            github=mock_github_instance,
        )

        # Verify the update was called
        mock_github_instance.update_pull_request.assert_called_once()
        call_args = mock_github_instance.update_pull_request.call_args
        body = call_args[1]["body"]

        # Verify content order
        title_pos = body.find("# PR Title")
        desc1_pos = body.find("Description line 1")
        desc2_pos = body.find("Description line 2")
        start_pos = body.find(start_keyword)
        summary_pos = body.find("New summary")
        end_pos = body.find(end_keyword)
        testing_pos = body.find("## Testing")
        test_inst_pos = body.find("Test instructions here")

        # Check order
        assert title_pos < desc1_pos < desc2_pos < start_pos < summary_pos < end_pos < testing_pos < test_inst_pos

    def test_inject_with_multiline_injection_text(self, mock_github_instance):
        """Test injection with multiline content.

        When the injection text contains multiple lines with
        various formatting, it should be properly included in
        the collapsible section.

        Mocks:
            - Github instance to verify update_pull_request call
        """
        pr_node_id = "PR_kwDOABCDE123456789"
        injection_title = "Analysis"
        start_keyword = "<!-- analysis-start -->"
        end_keyword = "<!-- analysis-end -->"
        description_old = "Original description."
        injection_text = (
            "## Analysis Results\n\n"
            "- Point 1\n"
            "- Point 2\n\n"
            "```python\n"
            "def example():\n"
            "    pass\n"
            "```\n\n"
            "**Bold text** and *italic*."
        )

        inject_to_pull_request_description(
            pr_node_id=pr_node_id,
            injection_title=injection_title,
            start_keyword=start_keyword,
            end_keyword=end_keyword,
            description_old=description_old,
            injection_text=injection_text,
            github=mock_github_instance,
        )

        # Verify the update was called
        mock_github_instance.update_pull_request.assert_called_once()
        call_args = mock_github_instance.update_pull_request.call_args
        body = call_args[1]["body"]

        # Verify all parts of multiline text are present
        assert "## Analysis Results" in body
        assert "- Point 1" in body
        assert "- Point 2" in body
        assert "```python" in body
        assert "def example():" in body
        assert "**Bold text**" in body

    def test_inject_with_special_characters_in_text(self, mock_github_instance):
        """Test injection with special characters.

        When the injection text contains special characters,
        HTML entities, or markdown syntax, they should be
        preserved correctly in the output.

        Mocks:
            - Github instance to verify update_pull_request call
        """
        pr_node_id = "PR_kwDOABCDE123456789"
        injection_title = "Special <Content>"
        start_keyword = "<!-- special-start -->"
        end_keyword = "<!-- special-end -->"
        description_old = "Original."
        injection_text = 'Content with <tags>, &amp; entities, and "quotes"'

        inject_to_pull_request_description(
            pr_node_id=pr_node_id,
            injection_title=injection_title,
            start_keyword=start_keyword,
            end_keyword=end_keyword,
            description_old=description_old,
            injection_text=injection_text,
            github=mock_github_instance,
        )

        # Verify the update was called
        mock_github_instance.update_pull_request.assert_called_once()
        call_args = mock_github_instance.update_pull_request.call_args
        body = call_args[1]["body"]

        # Special characters should be preserved
        assert "<tags>" in body
        assert "&amp;" in body
        assert '"quotes"' in body
        assert "Special <Content>" in body

    def test_inject_multiple_times_to_same_description(self, mock_github_instance):
        """Test injecting multiple times updates correctly.

        When inject is called multiple times on the same description
        (simulated by updating the description_old parameter),
        each call should properly update the section without
        duplicating markers or content.

        Mocks:
            - Github instance to verify update_pull_request calls
        """
        pr_node_id = "PR_kwDOABCDE123456789"
        injection_title = "Summary"
        start_keyword = "<!-- summary-start -->"
        end_keyword = "<!-- summary-end -->"
        description_old = "Original description."

        # First injection
        injection_text_1 = "First summary."
        inject_to_pull_request_description(
            pr_node_id=pr_node_id,
            injection_title=injection_title,
            start_keyword=start_keyword,
            end_keyword=end_keyword,
            description_old=description_old,
            injection_text=injection_text_1,
            github=mock_github_instance,
        )

        # Get the updated description
        first_body = mock_github_instance.update_pull_request.call_args[1]["body"]

        # Second injection with updated description
        mock_github_instance.reset_mock()
        injection_text_2 = "Second summary."
        inject_to_pull_request_description(
            pr_node_id=pr_node_id,
            injection_title=injection_title,
            start_keyword=start_keyword,
            end_keyword=end_keyword,
            description_old=first_body,
            injection_text=injection_text_2,
            github=mock_github_instance,
        )

        # Verify second update
        second_body = mock_github_instance.update_pull_request.call_args[1]["body"]

        # Should only have one set of markers
        assert second_body.count(start_keyword) == 1
        assert second_body.count(end_keyword) == 1

        # Should have new content, not old
        assert "Second summary." in second_body
        assert "First summary." not in second_body

    def test_inject_with_different_keyword_patterns(self, mock_github_instance):
        """Test injection with various keyword patterns.

        The function should work with different marker styles,
        including HTML comments, special tags, or custom markers.

        Mocks:
            - Github instance to verify update_pull_request call
        """
        pr_node_id = "PR_kwDOABCDE123456789"
        injection_title = "Results"
        start_keyword = "[RESULTS_START]"
        end_keyword = "[RESULTS_END]"
        description_old = "Description text."
        injection_text = "Results content."

        inject_to_pull_request_description(
            pr_node_id=pr_node_id,
            injection_title=injection_title,
            start_keyword=start_keyword,
            end_keyword=end_keyword,
            description_old=description_old,
            injection_text=injection_text,
            github=mock_github_instance,
        )

        # Verify the update was called
        mock_github_instance.update_pull_request.assert_called_once()
        call_args = mock_github_instance.update_pull_request.call_args
        body = call_args[1]["body"]

        # Custom keywords should be present
        assert "[RESULTS_START]" in body
        assert "[RESULTS_END]" in body
        assert injection_text in body
