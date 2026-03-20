"""Batch analysis tools for evaluating multiple GitHub pull requests.

This module provides functionality to analyze multiple pull requests simultaneously
against specific objectives, helping identify related changes, potential conflicts,
or patterns across different repositories and development efforts.
"""

from typing import Any

from ai_tools_base import LLMInterface, LoggingInterface, LogLevel
from pydantic import BaseModel, Field

from ai_tools_github.github_client import Github

from .utils.diff import filter_large_diff_chunks


class BatchPullRequestAnalysisInput(BaseModel):
    """Input schema for analyzing multiple pull requests against a specific objective.

    Defines the pull requests to analyze and the analysis criteria to evaluate
    them against, enabling batch processing and comparison of multiple changes.
    """

    pull_requests: list[dict[str, Any]] = Field(
        description="List of pull requests to analyze. Each dictionary should contain 'owner', 'repo', "
        "and 'number' keys.",
        examples=[
            [
                {"owner": "swh", "repo": "ddad", "number": 123},
                {"owner": "swh", "repo": "ddad", "number": 124},
                {"owner": "software-factory", "repo": "xpad-shared", "number": 456},
            ]
        ],
    )
    analysis_objective: str = Field(
        description="The analysis objective to evaluate against all pull request diffs. Be verbose about the request.",
        examples=[
            "Analyze the following error: ImportError: cannot import name 'missing_function' from 'module'",
            "Analyze the following error: TypeError: unsupported operand type(s) for +: 'int' and 'str'",
            "Analyze the following error: Build failed: undefined reference to 'function_name'",
            "Summarize the pull requests",
            "Which pull requests change something in the bootup process?",
        ],
    )


async def batch_analyze_pull_request(
    pull_requests: list[dict[str, Any]],
    analysis_objective: str,
    github: Github,
    llm: LLMInterface,
    logging: LoggingInterface,
) -> str:
    """Analyze multiple pull request diffs against a specific objective to identify relationships and patterns.

    This function performs intelligent analysis of multiple pull requests by comparing their
    code changes against a specific analysis objective. It helps identify which PRs might be
    related to specific errors, features, or patterns, providing a consolidated report with
    likelihood ratings and detailed analysis.

    The analysis is particularly useful for:
    - Root cause analysis: Finding PRs that might have introduced specific errors
    - Feature tracking: Identifying related changes across repositories
    - Impact assessment: Understanding which changes affect specific components
    - Dependency analysis: Finding changes that might conflict or interact

    Args:
        pull_requests: List of pull request identifiers to analyze. Each dictionary must
                      contain 'owner' (repository owner), 'repo' (repository name), and
                      'number' (pull request number) keys.
        analysis_objective: Detailed description of what to analyze for across all PRs.
                           Should be verbose and specific about the criteria, error messages,
                           or patterns to look for in the code changes.
        github: Authenticated GitHub instance for accessing repository data and diffs.
        llm: Large Language Model interface for intelligent analysis of code changes
             and pattern matching against the objective.
        logging: Logging interface for progress reporting and error tracking during
                the batch analysis process.

    Returns:
        A comprehensive report containing:
        - Individual analysis of each pull request against the objective
        - Likelihood ratings for relevance to the analysis objective
        - Summary of patterns and relationships found across the PRs
        - Recommendations for further investigation or action

    Raises:
        Exception: If GitHub access fails, pull requests cannot be retrieved, or
                  LLM analysis fails for any of the pull requests.

    Example:
        >>> pull_requests = [
        ...     {"owner": "myorg", "repo": "backend", "number": 42},
        ...     {"owner": "myorg", "repo": "frontend", "number": 17},
        ... ]
        >>> objective = "Find changes related to user authentication errors"
        >>> result = await batch_analyze_pull_request(
        ...     pull_requests=pull_requests,
        ...     analysis_objective=objective,
        ...     github=my_github_client,
        ...     llm=my_llm_interface,
        ...     logging=my_logging_interface
        ... )
        >>> print(result)
        # Analysis Report
        ## PR myorg/backend#42 - High Relevance (85%)
        This PR modifies the authentication middleware...
    """
    try:
        analyses: list[dict[str, str]] = []
        total_prs = len(pull_requests)

        # Report initial progress
        await logging.areport_progress(0, total_prs, f"Starting analysis of {total_prs} pull requests")

        for i, pr_dict in enumerate(pull_requests, 1):
            # Extract PR details from dictionary
            owner = pr_dict["owner"]
            repo = pr_dict["repo"]
            number = pr_dict["number"]

            # Report progress at the start of each PR analysis
            await logging.areport_progress(
                i - 1, total_prs, f"({i}/{total_prs}) Analyzing PR {i}/{total_prs}: {owner}/{repo}#{number}"
            )

            await logging.ainfo(f"({i}/{total_prs}) Analyzing PR {i}/{total_prs}: {owner}/{repo}#{number}")

            try:
                # Get the pull request diff
                pr_diff = github.pull_request_diff(
                    owner=owner,
                    repo=repo,
                    number=number,
                )

                pr_diff = filter_large_diff_chunks(pr_diff, max_lines=200)

                # Update progress after fetching diff
                await logging.areport_progress(
                    i,
                    total_prs,
                    f"({i}/{total_prs}) Fetched diff for {owner}/{repo}#{number}, running AI analysis...",
                )  # Use LLM to analyze the diff against the analysis objective
                analysis_prompt = f"""
                You are analyzing a pull request diff to determine if it could be related to a specific
                analysis objective.

                Analysis Objective:
                {analysis_objective}

                Pull Request Diff:
                {pr_diff}

                Please analyze the diff and determine:
                1. Could this pull request be related to the analysis objective?
                2. What specific changes in the diff might cause or fix the issue related to the analysis objective?
                3. Rate the likelihood (High/Medium/Low) that this PR is related to the
                   analysis objective
                4. Provide a brief explanation of your reasoning

                Focus on:
                - Function/variable names mentioned in the analysis objective
                - File paths or modules referenced in the analysis objective
                - Type changes, imports, or deletions that could cause the issue
                - Any code patterns that match the issue type

                Keep your response concise but informative.
                """

                analysis_result = await llm.ainvoke(analysis_prompt)

                analyses.append(
                    {
                        "pr": f"{owner}/{repo}#{number}",
                        "analysis": analysis_result,
                    }
                )

                # Report completion of this PR
                await logging.areport_progress(
                    i, total_prs, f"({i}/{total_prs}) Completed analysis of {owner}/{repo}#{number}"
                )

            except Exception as e:
                await logging.alog(f"Error analyzing PR {owner}/{repo}#{number}: {str(e)}", level=LogLevel.ERROR)
                analyses.append({"pr": f"{owner}/{repo}#{number}", "analysis": f"Error analyzing this PR: {str(e)}"})

                # Report error but continue
                await logging.areport_progress(
                    i, total_prs, f"({i}/{total_prs}) Error analyzing {owner}/{repo}#{number}, continuing..."
                )

        # Report final progress
        await logging.areport_progress(total_prs, total_prs, "Generating consolidated report...")

        # Create consolidated report
        report = "# Batch Pull Request Error Analysis\n\n"
        report += f"**Analysis Objective:** {analysis_objective}\n\n"
        report += f"**Analyzed {len(pull_requests)} pull requests:**\n\n"

        for analysis in analyses:
            report += f"## {analysis['pr']}\n\n"
            report += f"{analysis['analysis']}\n\n"
            report += "---\n\n"

        return report

    except Exception as e:
        await logging.alog(f"Error occurred during batch analysis of pull requests: {str(e)}", level=LogLevel.ERROR)
        return f"Error during batch analysis: {str(e)}"
