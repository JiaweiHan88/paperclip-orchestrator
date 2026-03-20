"""Test cases for pull_requests module."""

from datetime import datetime
import pytest

from ai_tools_github.models.pull_request import (
    Author,
    CheckRun,
    Commit,
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
)
from ai_tools_github.pull_request_state import pull_request_state_to_markdown


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
    return MergeCommit(
        oid="abc123",
        committed_date=datetime(2025, 11, 1, 12, 0, 0),
        typename="MergeCommit",
    )


@pytest.fixture
def sample_commits():
    """Create a list of sample Commit objects."""
    return [
        Commit(
            oid="abc123",
            typename="Commit",
            message_headline="Initial commit",
            message_body="",
            status_check_rollup=StatusCheckRollup(contexts=[]),
        )
    ]


@pytest.fixture
def sample_pull_request(sample_author, sample_repository, sample_merge_commit, sample_commits):
    """Create a sample PullRequest object."""
    pr = PullRequest(
        number=42,
        title="Fix bug in authentication",
        body="This PR fixes a critical bug in the authentication module.",
        base_ref_name="main",
        head_ref_name="fix/auth-bug",
        head_ref_oid="def456",
        url="https://github.com/test-owner/test-repo/pull/42",
        id="PR_1234567890",
        closed=False,
        merged=False,
        is_draft=False,
        mergeable="MERGEABLE",
        merge_commit=sample_merge_commit,
        review_decision="APPROVED",
        additions=50,
        deletions=20,
        reviews=[],
        labels=[Label(name="bug", color="red", typename="Label")],
        participants=[],
        author=sample_author,
        repository=sample_repository,
        comments=[],
        commits=sample_commits,
        typename="PullRequest",
        review_requests=[],
    )
    return pr


class TestPullRequestStateToMarkdown:
    """Tests for pull_request_state_to_markdown helper function."""

    def test_pr_state_markdown(self, sample_pull_request):
        """Test markdown generation for pull request with state info."""

        result = pull_request_state_to_markdown(sample_pull_request)

        assert "## Pull Request State Analysis" in result

    def test_status_checks_check_run_and_context(self, sample_author, sample_repository):
        """Status checks include both CheckRun and StatusContext entries."""

        check_run = CheckRun(
            name="lint",
            status="COMPLETED",
            conclusion="SUCCESS",
            summary=None,
            completed_at=datetime(2025, 11, 1, 12, 0, 0),
            typename="CheckRun",
        )
        status_context = StatusContext(context="ci/build", state="SUCCESS", typename="StatusContext")
        commits = [
            Commit(
                oid="abc",
                typename="Commit",
                message_headline="h",
                message_body="",
                status_check_rollup=StatusCheckRollup(
                    contexts=[check_run, status_context], typename="StatusCheckRollup"
                ),
            )
        ]
        pr = PullRequest(
            number=1,
            title="t",
            body="b",
            base_ref_name="main",
            head_ref_name="feature",
            head_ref_oid="abc",
            url="u",
            id="id",
            closed=False,
            merged=False,
            is_draft=False,
            mergeable="MERGEABLE",
            merge_commit=None,
            review_decision=None,
            additions=0,
            deletions=0,
            reviews=[],
            review_requests=[],
            labels=[],
            participants=[],
            author=sample_author,
            repository=sample_repository,
            comments=[],
            commits=commits,
            typename="PullRequest",
        )

        md = pull_request_state_to_markdown(pr)

        assert "### **lint** (completed at 2025-11-01 12:00:00): COMPLETED - SUCCESS" in md
        assert "### **ci/build**: SUCCESS" in md

    def test_labels_and_description_defaults(self, sample_pull_request):
        """Labels are listed and description falls back when absent."""

        pr = sample_pull_request.model_copy(update={"body": None})
        md = pull_request_state_to_markdown(pr)

        assert "### Labels:" in md
        assert "- bug" in md
        assert "No description provided." in md

    def test_approvals_and_missing_requests(self, sample_author, sample_repository):
        """Approved reviewers and missing code owner reviews are rendered."""

        reviewer_author = Author(login="approver", typename="Author")
        approvals = [
            Review(
                author=reviewer_author,
                state="APPROVED",
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                body="ok",
                id="r1",
                typename="Review",
            )
        ]
        review_requests = [
            ReviewRequest(
                as_code_owner=True, requested_reviewer=User(login="missing", typename="User"), typename="Review"
            ),
            ReviewRequest(
                as_code_owner=True, requested_reviewer=Team(name="core-team", typename="Team"), typename="Review"
            ),
        ]
        pr = PullRequest(
            number=2,
            title="t",
            body="desc",
            base_ref_name="main",
            head_ref_name="feature",
            head_ref_oid="",
            url="u",
            id="id",
            closed=False,
            merged=False,
            is_draft=False,
            mergeable="MERGEABLE",
            merge_commit=None,
            review_decision=None,
            additions=0,
            deletions=0,
            reviews=approvals,
            review_requests=review_requests,
            labels=[],
            participants=[],
            author=sample_author,
            repository=sample_repository,
            comments=[],
            commits=[],
            typename="PullRequest",
        )

        md = pull_request_state_to_markdown(pr)

        assert "### Current Reviews:" in md
        assert "approver" in md
        assert "APPROVED" in md
        assert "### Missing Approvals:" in md
        assert "missing" in md
        assert "core-team" in md

    @pytest.mark.parametrize(
        "closed,merged,is_draft,expected",
        [
            (False, False, True, "Draft"),
            (False, True, False, "Merged"),
            (True, False, False, "Closed"),
            (False, False, False, "Open"),
        ],
    )
    def test_pr_state_label(self, sample_pull_request, closed, merged, is_draft, expected):
        """Pull request state label matches flags."""

        pr = sample_pull_request.model_copy(update={"closed": closed, "merged": merged, "is_draft": is_draft})
        md = pull_request_state_to_markdown(pr)

        assert f"Pull Request State: {expected}" in md

    def test_no_status_checks(self, sample_author, sample_repository):
        """Test PR with no status checks."""
        commits = [
            Commit(
                oid="abc",
                typename="Commit",
                message_headline="h",
                message_body="",
                status_check_rollup=None,
            )
        ]
        pr = PullRequest(
            number=1,
            title="No checks",
            body="PR with no status checks",
            base_ref_name="main",
            head_ref_name="feature",
            head_ref_oid="abc",
            url="u",
            id="id",
            closed=False,
            merged=False,
            is_draft=False,
            mergeable="MERGEABLE",
            merge_commit=None,
            review_decision=None,
            additions=0,
            deletions=0,
            reviews=[],
            review_requests=[],
            labels=[],
            participants=[],
            author=sample_author,
            repository=sample_repository,
            comments=[],
            commits=commits,
            typename="PullRequest",
        )

        md = pull_request_state_to_markdown(pr)
        assert "### Status Checks:" not in md

    def test_multiple_labels(self, sample_author, sample_repository):
        """Test PR with multiple labels."""
        labels = [
            Label(name="bug", color="red", typename="Label"),
            Label(name="enhancement", color="blue", typename="Label"),
            Label(name="documentation", color="green", typename="Label"),
        ]
        pr = PullRequest(
            number=5,
            title="Multi-label PR",
            body="Has multiple labels",
            base_ref_name="main",
            head_ref_name="feature",
            head_ref_oid="",
            url="u",
            id="id",
            closed=False,
            merged=False,
            is_draft=False,
            mergeable="MERGEABLE",
            merge_commit=None,
            review_decision=None,
            additions=0,
            deletions=0,
            reviews=[],
            review_requests=[],
            labels=labels,
            participants=[],
            author=sample_author,
            repository=sample_repository,
            comments=[],
            commits=[],
            typename="PullRequest",
        )

        md = pull_request_state_to_markdown(pr)
        assert "- bug" in md
        assert "- enhancement" in md
        assert "- documentation" in md

    def test_multiple_approvals(self, sample_author, sample_repository):
        """Test PR with multiple approvals."""
        approvals = [
            Review(
                author=Author(login="reviewer1", typename="Author"),
                state="APPROVED",
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                body="Looks good",
                id="r1",
                typename="Review",
            ),
            Review(
                author=Author(login="reviewer2", typename="Author"),
                state="APPROVED",
                created_at=datetime(2024, 1, 2, 12, 0, 0),
                body="LGTM",
                id="r2",
                typename="Review",
            ),
        ]
        pr = PullRequest(
            number=3,
            title="Multi-approval PR",
            body="Multiple approvals",
            base_ref_name="main",
            head_ref_name="feature",
            head_ref_oid="",
            url="u",
            id="id",
            closed=False,
            merged=False,
            is_draft=False,
            mergeable="MERGEABLE",
            merge_commit=None,
            review_decision="APPROVED",
            additions=0,
            deletions=0,
            reviews=approvals,
            review_requests=[],
            labels=[],
            participants=[],
            author=sample_author,
            repository=sample_repository,
            comments=[],
            commits=[],
            typename="PullRequest",
        )

        md = pull_request_state_to_markdown(pr)
        assert "reviewer1" in md
        assert "reviewer2" in md
        assert md.count("**") >= 4  # At least two author names bolded

    def test_required_checks_in_markdown(self, sample_author, sample_repository):
        """Test that required status checks are displayed correctly."""
        check_run = CheckRun(
            name="build",
            status="COMPLETED",
            conclusion="SUCCESS",
            summary=None,
            completed_at=None,
        )
        commits = [
            Commit(
                oid="abc",
                typename="Commit",
                message_headline="h",
                message_body="",
                status_check_rollup=StatusCheckRollup(contexts=[check_run]),
            )
        ]
        pr = PullRequest(
            number=1,
            title="t",
            body="b",
            base_ref_name="main",
            head_ref_name="feature",
            head_ref_oid="abc",
            url="u",
            id="id",
            closed=False,
            merged=False,
            is_draft=False,
            mergeable="MERGEABLE",
            merge_commit=None,
            review_decision=None,
            additions=0,
            deletions=0,
            reviews=[],
            review_requests=[],
            labels=[],
            participants=[],
            author=sample_author,
            repository=sample_repository,
            comments=[],
            commits=commits,
            typename="PullRequest",
        )

        # Test with required checks
        required_checks = {"build", "test"}
        md = pull_request_state_to_markdown(pr, required_checks)

        assert "[REQUIRED]" in md
        assert "build" in md
        assert "NOT STARTED" in md  # test check not yet started

    def test_no_commits(self, sample_author, sample_repository):
        """Test PR with no commits."""
        pr = PullRequest(
            number=1,
            title="No commits",
            body="Empty PR",
            base_ref_name="main",
            head_ref_name="feature",
            head_ref_oid="",
            url="u",
            id="id",
            closed=False,
            merged=False,
            is_draft=False,
            mergeable="MERGEABLE",
            merge_commit=None,
            review_decision=None,
            additions=0,
            deletions=0,
            reviews=[],
            review_requests=[],
            labels=[],
            participants=[],
            author=sample_author,
            repository=sample_repository,
            comments=[],
            commits=[],
            typename="PullRequest",
        )

        md = pull_request_state_to_markdown(pr)
        assert "## Pull Request State Analysis" in md

    def test_review_state_changes(self, sample_author, sample_repository):
        """Test different review states (APPROVED, COMMENTED, CHANGES_REQUESTED)."""
        reviews = [
            Review(
                author=Author(login="approver", typename="Author"),
                state="APPROVED",
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                body="",
                id="r1",
                typename="Review",
            ),
            Review(
                author=Author(login="commenter", typename="Author"),
                state="COMMENTED",
                created_at=datetime(2024, 1, 2, 12, 0, 0),
                body="Need more info",
                id="r2",
                typename="Review",
            ),
        ]
        pr = PullRequest(
            number=1,
            title="t",
            body="b",
            base_ref_name="main",
            head_ref_name="feature",
            head_ref_oid="",
            url="u",
            id="id",
            closed=False,
            merged=False,
            is_draft=False,
            mergeable="MERGEABLE",
            merge_commit=None,
            review_decision=None,
            additions=0,
            deletions=0,
            reviews=reviews,
            review_requests=[],
            labels=[],
            participants=[],
            author=sample_author,
            repository=sample_repository,
            comments=[],
            commits=[],
            typename="PullRequest",
        )

        md = pull_request_state_to_markdown(pr)
        assert "approver" in md
        # All reviews should be in Current Reviews section with their state
        assert md.count("approver") >= 1
