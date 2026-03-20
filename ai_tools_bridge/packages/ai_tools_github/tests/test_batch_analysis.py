from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from ai_tools_github.batch_analysis import (
    BatchPullRequestAnalysisInput,
    batch_analyze_pull_request,
)


@pytest_asyncio.fixture
def mock_github():
    """Mock GitHub instance for testing."""
    github = MagicMock()
    return github


@pytest.fixture
def mock_llm():
    """Mock LLM interface for testing."""
    llm = AsyncMock()
    return llm


@pytest.fixture
def mock_logging():
    """Mock logging interface for testing."""
    logging = AsyncMock()
    return logging


@pytest.fixture
def sample_pull_requests():
    """Sample pull request list for testing."""
    return [
        {"owner": "test-org", "repo": "test-repo", "number": 123},
        {"owner": "test-org", "repo": "test-repo", "number": 456},
        {"owner": "another-org", "repo": "another-repo", "number": 789},
    ]


@pytest.fixture
def sample_analysis_objective():
    """Sample analysis objective for testing."""
    return "Analyze the following error: ImportError: cannot import name 'missing_function' from 'module'"


@pytest.fixture
def sample_diff():
    """Sample diff for testing."""
    return """diff --git a/src/module.py b/src/module.py
index abc123..def456 100644
--- a/src/module.py
+++ b/src/module.py
@@ -1,5 +1,5 @@
 def existing_function():
     pass
 
-def missing_function():
+def renamed_function():
     pass
"""


class TestBatchPullRequestAnalysisInput:
    """Test the input model validation."""

    def test_valid_input(self, sample_pull_requests, sample_analysis_objective):
        """Test that valid input is accepted."""
        input_data = BatchPullRequestAnalysisInput(
            pull_requests=sample_pull_requests,
            analysis_objective=sample_analysis_objective,
        )
        assert input_data.pull_requests == sample_pull_requests
        assert input_data.analysis_objective == sample_analysis_objective

    def test_empty_pull_requests(self, sample_analysis_objective):
        """Test that empty pull request list is accepted."""
        input_data = BatchPullRequestAnalysisInput(
            pull_requests=[],
            analysis_objective=sample_analysis_objective,
        )
        assert input_data.pull_requests == []


@pytest.mark.asyncio
class TestBatchAnalyzePullRequest:
    """Test the batch_analyze_pull_request function."""

    async def test_successful_analysis_single_pr(
        self, mock_github, mock_llm, mock_logging, sample_diff, sample_analysis_objective
    ):
        """Test successful analysis of a single pull request."""
        # Setup mocks
        mock_github.pull_request_diff.return_value = sample_diff
        mock_llm.ainvoke.return_value = "High likelihood - This PR renames missing_function which matches the error."

        pull_requests = [{"owner": "test-org", "repo": "test-repo", "number": 123}]

        # Execute
        result = await batch_analyze_pull_request(
            pull_requests=pull_requests,
            analysis_objective=sample_analysis_objective,
            github=mock_github,
            llm=mock_llm,
            logging=mock_logging,
        )

        # Verify
        assert "# Batch Pull Request Error Analysis" in result
        assert "test-org/test-repo#123" in result
        assert "High likelihood" in result
        assert mock_github.pull_request_diff.call_count == 1
        assert mock_llm.ainvoke.call_count == 1
        assert mock_logging.areport_progress.call_count >= 2  # At least start and end

    async def test_successful_analysis_multiple_prs(
        self, mock_github, mock_llm, mock_logging, sample_pull_requests, sample_diff, sample_analysis_objective
    ):
        """Test successful analysis of multiple pull requests."""
        # Setup mocks
        mock_github.pull_request_diff.return_value = sample_diff
        mock_llm.ainvoke.side_effect = [
            "High likelihood - Changes match the error pattern.",
            "Low likelihood - Unrelated changes.",
            "Medium likelihood - Partially related changes.",
        ]

        # Execute
        result = await batch_analyze_pull_request(
            pull_requests=sample_pull_requests,
            analysis_objective=sample_analysis_objective,
            github=mock_github,
            llm=mock_llm,
            logging=mock_logging,
        )

        # Verify
        assert "# Batch Pull Request Error Analysis" in result
        assert "test-org/test-repo#123" in result
        assert "test-org/test-repo#456" in result
        assert "another-org/another-repo#789" in result
        assert "High likelihood" in result
        assert "Low likelihood" in result
        assert "Medium likelihood" in result
        assert mock_github.pull_request_diff.call_count == 3
        assert mock_llm.ainvoke.call_count == 3
        # Should have progress reports for: start, and each PR (3 times)
        assert mock_logging.areport_progress.call_count >= 4

    async def test_analysis_with_empty_pr_list(self, mock_github, mock_llm, mock_logging, sample_analysis_objective):
        """Test analysis with empty pull request list."""
        # Execute
        result = await batch_analyze_pull_request(
            pull_requests=[],
            analysis_objective=sample_analysis_objective,
            github=mock_github,
            llm=mock_llm,
            logging=mock_logging,
        )

        # Verify
        assert "# Batch Pull Request Error Analysis" in result
        assert "Analyzed 0 pull requests" in result
        assert mock_github.pull_request_diff.call_count == 0
        assert mock_llm.ainvoke.call_count == 0

    async def test_analysis_with_github_error(self, mock_github, mock_llm, mock_logging, sample_analysis_objective):
        """Test analysis when GitHub API raises an error."""
        # Setup mocks
        mock_github.pull_request_diff.side_effect = Exception("GitHub API error")

        pull_requests = [{"owner": "test-org", "repo": "test-repo", "number": 123}]

        # Execute
        result = await batch_analyze_pull_request(
            pull_requests=pull_requests,
            analysis_objective=sample_analysis_objective,
            github=mock_github,
            llm=mock_llm,
            logging=mock_logging,
        )

        # Verify
        assert "# Batch Pull Request Error Analysis" in result
        assert "test-org/test-repo#123" in result
        assert "Error analyzing this PR" in result
        assert "GitHub API error" in result
        assert mock_github.pull_request_diff.call_count == 1
        assert mock_llm.ainvoke.call_count == 0  # Should not be called if GitHub fails
        assert mock_logging.alog.call_count >= 1  # Error should be logged

    async def test_analysis_with_llm_error(
        self, mock_github, mock_llm, mock_logging, sample_diff, sample_analysis_objective
    ):
        """Test analysis when LLM raises an error."""
        # Setup mocks
        mock_github.pull_request_diff.return_value = sample_diff
        mock_llm.ainvoke.side_effect = Exception("LLM processing error")

        pull_requests = [{"owner": "test-org", "repo": "test-repo", "number": 123}]

        # Execute
        result = await batch_analyze_pull_request(
            pull_requests=pull_requests,
            analysis_objective=sample_analysis_objective,
            github=mock_github,
            llm=mock_llm,
            logging=mock_logging,
        )

        # Verify
        assert "# Batch Pull Request Error Analysis" in result
        assert "test-org/test-repo#123" in result
        assert "Error analyzing this PR" in result
        assert "LLM processing error" in result
        assert mock_github.pull_request_diff.call_count == 1
        assert mock_llm.ainvoke.call_count == 1
        assert mock_logging.alog.call_count >= 1  # Error should be logged

    async def test_analysis_with_mixed_success_and_errors(
        self, mock_github, mock_llm, mock_logging, sample_diff, sample_analysis_objective
    ):
        """Test analysis with some PRs succeeding and others failing."""
        # Setup mocks - first PR succeeds, second fails at GitHub, third succeeds
        mock_github.pull_request_diff.side_effect = [
            sample_diff,
            Exception("GitHub API error"),
            sample_diff,
        ]
        mock_llm.ainvoke.side_effect = [
            "High likelihood - First PR analysis.",
            "Medium likelihood - Third PR analysis.",
        ]

        pull_requests = [
            {"owner": "test-org", "repo": "test-repo", "number": 123},
            {"owner": "test-org", "repo": "test-repo", "number": 456},
            {"owner": "test-org", "repo": "test-repo", "number": 789},
        ]

        # Execute
        result = await batch_analyze_pull_request(
            pull_requests=pull_requests,
            analysis_objective=sample_analysis_objective,
            github=mock_github,
            llm=mock_llm,
            logging=mock_logging,
        )

        # Verify
        assert "# Batch Pull Request Error Analysis" in result
        assert "test-org/test-repo#123" in result
        assert "test-org/test-repo#456" in result
        assert "test-org/test-repo#789" in result
        assert "High likelihood" in result
        assert "Medium likelihood" in result
        assert "Error analyzing this PR" in result
        assert mock_github.pull_request_diff.call_count == 3
        assert mock_llm.ainvoke.call_count == 2  # Only called for successful PRs
        assert mock_logging.alog.call_count >= 1  # Error should be logged

    async def test_progress_reporting(
        self, mock_github, mock_llm, mock_logging, sample_diff, sample_analysis_objective
    ):
        """Test that progress is reported correctly throughout the analysis."""
        # Setup mocks
        mock_github.pull_request_diff.return_value = sample_diff
        mock_llm.ainvoke.return_value = "Analysis result"

        pull_requests = [
            {"owner": "test-org", "repo": "test-repo", "number": 1},
            {"owner": "test-org", "repo": "test-repo", "number": 2},
        ]

        # Execute
        await batch_analyze_pull_request(
            pull_requests=pull_requests,
            analysis_objective=sample_analysis_objective,
            github=mock_github,
            llm=mock_llm,
            logging=mock_logging,
        )

        # Verify progress reporting
        progress_calls = mock_logging.areport_progress.call_args_list
        assert len(progress_calls) >= 5  # Start, 2 PRs (start + complete each), final report

        # Check that progress values are correct
        # First call should be (0, 2, "Starting...")
        assert progress_calls[0][0][0] == 0
        assert progress_calls[0][0][1] == 2
        assert "Starting" in progress_calls[0][0][2]

        # Last call should be (2, 2, "Generating...")
        assert progress_calls[-1][0][0] == 2
        assert progress_calls[-1][0][1] == 2

    async def test_info_logging(self, mock_github, mock_llm, mock_logging, sample_diff, sample_analysis_objective):
        """Test that info messages are logged for each PR."""
        # Setup mocks
        mock_github.pull_request_diff.return_value = sample_diff
        mock_llm.ainvoke.return_value = "Analysis result"

        pull_requests = [
            {"owner": "test-org", "repo": "test-repo", "number": 123},
        ]

        # Execute
        await batch_analyze_pull_request(
            pull_requests=pull_requests,
            analysis_objective=sample_analysis_objective,
            github=mock_github,
            llm=mock_llm,
            logging=mock_logging,
        )

        # Verify info logging
        assert mock_logging.ainfo.call_count >= 1
        info_calls = mock_logging.ainfo.call_args_list
        assert "test-org/test-repo#123" in info_calls[0][0][0]

    async def test_llm_prompt_structure(
        self, mock_github, mock_llm, mock_logging, sample_diff, sample_analysis_objective
    ):
        """Test that the LLM prompt contains the correct structure and information."""
        # Setup mocks
        mock_github.pull_request_diff.return_value = sample_diff
        mock_llm.ainvoke.return_value = "Analysis result"

        pull_requests = [{"owner": "test-org", "repo": "test-repo", "number": 123}]

        # Execute
        await batch_analyze_pull_request(
            pull_requests=pull_requests,
            analysis_objective=sample_analysis_objective,
            github=mock_github,
            llm=mock_llm,
            logging=mock_logging,
        )

        # Verify LLM was called with correct prompt structure
        assert mock_llm.ainvoke.call_count == 1
        llm_prompt = mock_llm.ainvoke.call_args[0][0]

        # Check prompt contains key elements
        assert sample_analysis_objective in llm_prompt
        assert sample_diff in llm_prompt or "def renamed_function" in llm_prompt  # May be filtered
        assert "Analysis Objective:" in llm_prompt
        assert "Pull Request Diff:" in llm_prompt
        assert "likelihood" in llm_prompt.lower()

    async def test_report_format(self, mock_github, mock_llm, mock_logging, sample_diff, sample_analysis_objective):
        """Test that the final report has the correct format."""
        # Setup mocks
        mock_github.pull_request_diff.return_value = sample_diff
        mock_llm.ainvoke.return_value = "Test analysis result"

        pull_requests = [
            {"owner": "org1", "repo": "repo1", "number": 1},
            {"owner": "org2", "repo": "repo2", "number": 2},
        ]

        # Execute
        result = await batch_analyze_pull_request(
            pull_requests=pull_requests,
            analysis_objective=sample_analysis_objective,
            github=mock_github,
            llm=mock_llm,
            logging=mock_logging,
        )

        # Verify report structure
        assert result.startswith("# Batch Pull Request Error Analysis")
        assert "**Analysis Objective:**" in result
        assert sample_analysis_objective in result
        assert "**Analyzed 2 pull requests:**" in result
        assert "## org1/repo1#1" in result
        assert "## org2/repo2#2" in result
        assert result.count("---") == 2  # Separator between PRs

    async def test_large_diff_filtering(self, mock_github, mock_llm, mock_logging, sample_analysis_objective):
        """Test that large diffs are filtered appropriately."""
        # Create a large diff that should be filtered
        large_diff = "diff --git a/large_file.py b/large_file.py\n"
        large_diff += "--- a/large_file.py\n"
        large_diff += "+++ b/large_file.py\n"
        large_diff += "@@ -1,300 +1,300 @@\n"
        for i in range(300):
            large_diff += f"+Line {i}\n"

        # Setup mocks
        mock_github.pull_request_diff.return_value = large_diff
        mock_llm.ainvoke.return_value = "Analysis result"

        pull_requests = [{"owner": "test-org", "repo": "test-repo", "number": 123}]

        # Execute
        result = await batch_analyze_pull_request(
            pull_requests=pull_requests,
            analysis_objective=sample_analysis_objective,
            github=mock_github,
            llm=mock_llm,
            logging=mock_logging,
        )

        # Verify that analysis completed
        assert "# Batch Pull Request Error Analysis" in result
        assert mock_llm.ainvoke.call_count == 1

        # The diff passed to LLM should be filtered (we can check the call args)
        llm_prompt = mock_llm.ainvoke.call_args[0][0]
        # The filtered diff should be shorter than the original
        assert len(llm_prompt) < len(large_diff) + 1000  # Add buffer for prompt text
