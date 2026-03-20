"""
Unit tests for the buildsets module.

This test module validates:
1. FetchZuulBuildsetsInput and Buildset model validation
2. get_zuul_buildsets_for_pr function with various scenarios
3. _extract_zuul_buildset_from_check_run helper function
4. Proper handling of GitHub API responses
5. Buildset extraction from check runs
"""

from unittest.mock import Mock
from unittest import TestCase

from ai_tools_github.github_client import Github
from ai_tools_github.github_types import CheckConclusionState, CheckStatusState
from ai_tools_github.models.pull_request import (
    CheckRun,
    Commit,
    PullRequest,
    StatusCheckRollup,
)

from ai_tools_github.buildsets import (
    FetchZuulBuildsetsInput,
    ZuulCheckRun,
    FetchZuulBuildsetsOutput,
    get_zuul_buildsets_for_pr,
    _extract_zuul_buildset_from_check_run,
)


class TestBuildsetModels(TestCase):
    """Test the Pydantic models for buildsets."""

    def test_fetch_zuul_buildsets_input_valid(self):
        """Test FetchZuulBuildsetsInput with valid data."""
        input_data = FetchZuulBuildsetsInput(
            owner="test-owner",
            repo="test-repo",
            number=42,
        )

        self.assertEqual(input_data.owner, "test-owner")
        self.assertEqual(input_data.repo, "test-repo")
        self.assertEqual(input_data.number, 42)

    def test_buildset_valid_full(self):
        """Test Buildset with all fields."""
        buildset = ZuulCheckRun(
            pipeline="check-jobs",
            buildset_id="abc123",
            tenant="my-tenant",
            status="completed",
            conclusion="success",
            summary="All jobs passed",
        )

        self.assertEqual(buildset.pipeline, "check-jobs")
        self.assertEqual(buildset.buildset_id, "abc123")
        self.assertEqual(buildset.tenant, "my-tenant")
        self.assertEqual(buildset.status, "completed")
        self.assertEqual(buildset.conclusion, "success")
        self.assertEqual(buildset.summary, "All jobs passed")

    def test_buildset_valid_all_fields_provided(self):
        """Test Buildset with all fields provided (all are now mandatory)."""
        buildset = ZuulCheckRun(
            pipeline="gate-jobs",
            buildset_id="def456",
            tenant="test-tenant",
            status="QUEUED",
            conclusion="NEUTRAL",
            summary="Build queued",
        )

        self.assertEqual(buildset.pipeline, "gate-jobs")
        self.assertEqual(buildset.buildset_id, "def456")
        self.assertEqual(buildset.tenant, "test-tenant")
        self.assertEqual(buildset.status, "QUEUED")
        self.assertEqual(buildset.conclusion, "NEUTRAL")
        self.assertEqual(buildset.summary, "Build queued")

    def test_fetch_zuul_buildsets_output_empty(self):
        """Test FetchZuulBuildsetsOutput with empty list."""
        output = FetchZuulBuildsetsOutput()

        self.assertEqual(output.buildsets, [])

    def test_fetch_zuul_buildsets_output_with_buildsets(self):
        """Test FetchZuulBuildsetsOutput with buildsets."""
        output = FetchZuulBuildsetsOutput(
            buildsets=[
                ZuulCheckRun(
                    pipeline="check-jobs",
                    buildset_id="abc123",
                    tenant="tenant1",
                    status="COMPLETED",
                    conclusion="SUCCESS",
                    summary="Build passed",
                ),
                ZuulCheckRun(
                    pipeline="gate-jobs",
                    buildset_id="def456",
                    tenant="tenant1",
                    status="COMPLETED",
                    conclusion="FAILURE",
                    summary="Build failed",
                ),
            ]
        )

        self.assertEqual(len(output.buildsets), 2)
        self.assertEqual(output.buildsets[0].pipeline, "check-jobs")
        self.assertEqual(output.buildsets[1].pipeline, "gate-jobs")


class TestExtractZuulBuildsetFromCheckRun(TestCase):
    """Test the _extract_zuul_buildset_from_check_run helper function."""

    def test_extract_zuul_buildset_with_name(self):
        """Test extraction when check run has 'zuul' in name."""
        check_run = CheckRun(
            name="zuul/check-jobs",
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.SUCCESS,
            summary="Build at https://example.com/zuul/t/tenant1/buildset/abc123def",
        )

        result = _extract_zuul_buildset_from_check_run(check_run)

        assert result is not None
        self.assertEqual(result["pipeline"], "zuul/check-jobs")
        self.assertEqual(result["type"], "zuul_check_run")
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["conclusion"], "SUCCESS")
        self.assertEqual(result["buildset_id"], "abc123def")
        self.assertEqual(result["tenant"], "tenant1")

    def test_extract_zuul_buildset_with_summary(self):
        """Test extraction when check run has 'zuul' in summary."""
        check_run = CheckRun(
            name="CI Build",
            status=CheckStatusState.IN_PROGRESS,
            conclusion=None,
            summary="Running zuul build at https://zuul.example.com/buildset/xyz789",
        )

        result = _extract_zuul_buildset_from_check_run(check_run)

        assert result is not None
        self.assertEqual(result["pipeline"], "CI Build")
        self.assertEqual(result["status"], "IN_PROGRESS")
        # Note: conclusion can still be None in the dict, validation happens when creating ZuulCheckRun
        self.assertIsNone(result["conclusion"])
        self.assertEqual(result["buildset_id"], "xyz789")

    def test_extract_zuul_buildset_no_name(self):
        """Test extraction when check run has no name."""
        check_run = CheckRun(
            name=None,
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.SUCCESS,
            summary="Some summary",
        )

        result = _extract_zuul_buildset_from_check_run(check_run)

        self.assertIsNone(result)

    def test_extract_zuul_buildset_not_zuul(self):
        """Test extraction when check run is not a Zuul check."""
        check_run = CheckRun(
            name="GitHub Actions CI",
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.SUCCESS,
            summary="Build completed successfully",
        )

        result = _extract_zuul_buildset_from_check_run(check_run)

        self.assertIsNone(result)

    def test_extract_zuul_buildset_no_buildset_id(self):
        """Test extraction when buildset ID cannot be found."""
        check_run = CheckRun(
            name="zuul-check",
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.FAILURE,
            summary="Build failed, no buildset link",
        )

        result = _extract_zuul_buildset_from_check_run(check_run)

        assert result is not None
        self.assertEqual(result["pipeline"], "zuul-check")
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["conclusion"], "FAILURE")
        self.assertNotIn("buildset_id", result)

    def test_extract_zuul_buildset_case_insensitive(self):
        """Test extraction is case-insensitive for 'zuul'."""
        check_run = CheckRun(
            name="Zuul/CHECK-jobs",
            status=CheckStatusState.QUEUED,
            conclusion=None,
            summary="Queued for execution",
        )

        result = _extract_zuul_buildset_from_check_run(check_run)

        assert result is not None
        self.assertEqual(result["pipeline"], "Zuul/CHECK-jobs")

    def test_extract_zuul_buildset_backslash_separator(self):
        """Test extraction with backslash separator in URLs."""
        check_run = CheckRun(
            name="zuul-gate",
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.SUCCESS,
            summary="Build at https://zuul.example.com\\t\\tenant2\\buildset\\ghi456jkl",
        )

        result = _extract_zuul_buildset_from_check_run(check_run)

        assert result is not None
        self.assertEqual(result["buildset_id"], "ghi456jkl")
        # The regex looks for zuul[/\\]t[/\\](\w+), so it won't match this pattern
        # This test should not expect to find a tenant
        self.assertNotIn("tenant", result)

    def test_extract_zuul_buildset_no_status(self):
        """Test extraction when status is None.

        Note: The extraction function returns a dict that may have None values.
        When this dict is used to create a ZuulCheckRun object, validation will
        fail if any required field is None. This test verifies the extraction
        behavior, not the final model validation.
        """
        check_run = CheckRun(
            name="zuul-test",
            status=None,
            conclusion=None,
            summary="Pending",
        )

        result = _extract_zuul_buildset_from_check_run(check_run)

        assert result is not None
        self.assertIsNone(result["status"])
        self.assertIsNone(result["conclusion"])

    def test_extract_zuul_buildset_no_summary(self):
        """Test extraction when summary is None."""
        check_run = CheckRun(
            name="zuul-build",
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.SUCCESS,
            summary=None,
        )

        result = _extract_zuul_buildset_from_check_run(check_run)

        assert result is not None
        self.assertEqual(result["pipeline"], "zuul-build")
        self.assertIsNone(result["summary"])
        self.assertNotIn("buildset_id", result)
        self.assertNotIn("tenant", result)


class TestGetZuulBuildsetsForPr(TestCase):
    """Test the get_zuul_buildsets_for_pr function."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_github = Mock(spec=Github)

    def test_get_zuul_buildsets_success(self):
        """Test successful retrieval of Zuul buildsets."""
        # Create mock check runs
        check_run1 = CheckRun(
            name="zuul/check-jobs",
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.SUCCESS,
            summary="Build at https://example.com/zuul/t/tenant1/buildset/abc123",
        )
        check_run2 = CheckRun(
            name="zuul/gate-jobs",
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.FAILURE,
            summary="Build at https://example.com/zuul/t/tenant1/buildset/def456",
        )

        # Create mock commit with status check rollup
        mock_commit = Commit(status_check_rollup=StatusCheckRollup(contexts=[check_run1, check_run2]))

        # Create mock pull request with commits directly
        mock_pr = PullRequest(commits=[mock_commit])

        self.mock_github.pull_request.return_value = mock_pr

        result = get_zuul_buildsets_for_pr(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=self.mock_github,
        )

        self.assertEqual(len(result.buildsets), 2)

        # Verify first buildset
        self.assertEqual(result.buildsets[0].pipeline, "zuul/check-jobs")
        self.assertEqual(result.buildsets[0].buildset_id, "abc123")
        # Tenant won't be extracted because summary has /t/tenant1 not /t/tenant1/ in correct format
        self.assertEqual(result.buildsets[0].tenant, "tenant1")
        self.assertEqual(result.buildsets[0].status, "COMPLETED")
        self.assertEqual(result.buildsets[0].conclusion, "SUCCESS")

        # Verify second buildset
        self.assertEqual(result.buildsets[1].pipeline, "zuul/gate-jobs")
        self.assertEqual(result.buildsets[1].buildset_id, "def456")
        self.assertEqual(result.buildsets[1].tenant, "tenant1")
        self.assertEqual(result.buildsets[1].status, "COMPLETED")
        self.assertEqual(result.buildsets[1].conclusion, "FAILURE")

    def test_get_zuul_buildsets_no_commits(self):
        """Test when pull request has no commits."""
        mock_pr = PullRequest(commits=[])
        self.mock_github.pull_request.return_value = mock_pr

        result = get_zuul_buildsets_for_pr(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=self.mock_github,
        )

        self.assertEqual(len(result.buildsets), 0)

    def test_get_zuul_buildsets_no_status_check_rollup(self):
        """Test when commit has no status check rollup."""
        mock_commit = Commit(status_check_rollup=None)
        mock_pr = PullRequest(commits=[mock_commit])

        self.mock_github.pull_request.return_value = mock_pr

        result = get_zuul_buildsets_for_pr(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=self.mock_github,
        )

        self.assertEqual(len(result.buildsets), 0)

    def test_get_zuul_buildsets_no_contexts(self):
        """Test when status check rollup has no contexts."""
        mock_commit = Commit(status_check_rollup=StatusCheckRollup(contexts=[]))
        mock_pr = PullRequest(commits=[mock_commit])

        self.mock_github.pull_request.return_value = mock_pr

        result = get_zuul_buildsets_for_pr(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=self.mock_github,
        )

        self.assertEqual(len(result.buildsets), 0)

    def test_get_zuul_buildsets_filters_non_zuul(self):
        """Test that non-Zuul check runs are filtered out."""
        # Create mix of Zuul and non-Zuul check runs
        zuul_check = CheckRun(
            name="zuul/check-jobs",
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.SUCCESS,
            summary="Build at https://zuul.example.com/t/tenant1/buildset/abc123",
        )
        other_check = CheckRun(
            name="GitHub Actions",
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.SUCCESS,
            summary="All checks passed",
        )

        mock_commit = Commit(status_check_rollup=StatusCheckRollup(contexts=[zuul_check, other_check]))
        mock_pr = PullRequest(commits=[mock_commit])

        self.mock_github.pull_request.return_value = mock_pr

        result = get_zuul_buildsets_for_pr(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=self.mock_github,
        )

        # Should only have the Zuul check run
        self.assertEqual(len(result.buildsets), 1)
        self.assertEqual(result.buildsets[0].pipeline, "zuul/check-jobs")

    def test_get_zuul_buildsets_multiple_commits(self):
        """Test that only the last commit is processed."""
        # Create first commit with Zuul check
        check_run1 = CheckRun(
            name="zuul/old-check",
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.SUCCESS,
            summary="Build at https://zuul.example.com/buildset/old123",
        )
        mock_commit1 = Commit(status_check_rollup=StatusCheckRollup(contexts=[check_run1]))

        # Create second commit with different Zuul check
        check_run2 = CheckRun(
            name="zuul/new-check",
            status=CheckStatusState.COMPLETED,
            conclusion=CheckConclusionState.SUCCESS,
            summary="Build at https://zuul.example.com/buildset/new456",
        )
        mock_commit2 = Commit(status_check_rollup=StatusCheckRollup(contexts=[check_run2]))

        mock_pr = PullRequest(commits=[mock_commit1, mock_commit2])
        self.mock_github.pull_request.return_value = mock_pr

        result = get_zuul_buildsets_for_pr(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=self.mock_github,
        )

        # Should only have the buildset from the last commit
        self.assertEqual(len(result.buildsets), 1)
        self.assertEqual(result.buildsets[0].pipeline, "zuul/new-check")
        self.assertEqual(result.buildsets[0].buildset_id, "new456")

    def test_get_zuul_buildsets_in_progress(self):
        """Test retrieval of in-progress buildsets.

        Note: Since ZuulCheckRun now requires all fields to be non-None,
        the implementation provides empty strings for fields that are None
        in the check run data.
        """
        check_run = CheckRun(
            name="zuul/check-jobs",
            status=CheckStatusState.IN_PROGRESS,
            conclusion=None,
            summary="Build running at https://zuul.example.com/buildset/inprog123",
        )

        mock_commit = Commit(status_check_rollup=StatusCheckRollup(contexts=[check_run]))
        mock_pr = PullRequest(commits=[mock_commit])

        self.mock_github.pull_request.return_value = mock_pr

        result = get_zuul_buildsets_for_pr(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=self.mock_github,
        )

        self.assertEqual(len(result.buildsets), 1)
        self.assertEqual(result.buildsets[0].status, "IN_PROGRESS")
        # Missing conclusion becomes empty string
        self.assertEqual(result.buildsets[0].conclusion, "")

    def test_get_zuul_buildsets_queued(self):
        """Test retrieval of queued buildsets.

        Note: Since all ZuulCheckRun fields are mandatory, the implementation
        provides empty strings for fields that are None or missing in the check run.
        """
        check_run = CheckRun(
            name="zuul/gate-jobs",
            status=CheckStatusState.QUEUED,
            conclusion=None,
            summary="Queued for execution",
        )

        mock_commit = Commit(status_check_rollup=StatusCheckRollup(contexts=[check_run]))
        mock_pr = PullRequest(commits=[mock_commit])

        self.mock_github.pull_request.return_value = mock_pr

        result = get_zuul_buildsets_for_pr(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=self.mock_github,
        )

        self.assertEqual(len(result.buildsets), 1)
        self.assertEqual(result.buildsets[0].status, "QUEUED")
        # Missing fields become empty strings
        self.assertEqual(result.buildsets[0].conclusion, "")
        self.assertEqual(result.buildsets[0].tenant, "")
        self.assertEqual(result.buildsets[0].buildset_id, "")

    def test_get_zuul_buildsets_api_called_correctly(self):
        """Test that GitHub API is called with correct parameters."""
        mock_pr = PullRequest(commits=[])
        self.mock_github.pull_request.return_value = mock_pr

        get_zuul_buildsets_for_pr(
            owner="test-owner",
            repo="test-repo",
            number=42,
            github=self.mock_github,
        )

        # Verify the API was called with correct parameters
        self.mock_github.pull_request.assert_called_once()
        call_args = self.mock_github.pull_request.call_args
        self.assertEqual(call_args.kwargs["owner"], "test-owner")
        self.assertEqual(call_args.kwargs["repo"], "test-repo")
        self.assertEqual(call_args.kwargs["number"], 42)
        self.assertEqual(call_args.kwargs["instance_class"], PullRequest)
        # Verify querydata contains the GraphQL query
        self.assertIn("statusCheckRollup", call_args.kwargs["querydata"])


if __name__ == "__main__":
    import unittest

    unittest.main()
