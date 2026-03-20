# AI Tools GitHub

AI tools for GitHub operations and repository management, providing comprehensive functionality for pull request analysis, diff retrieval, batch processing, and issue management.

## Overview

This package provides tools for interacting with GitHub repositories. Tools are defined using the framework-agnostic [`ToolDescription`](../ai_tools_base/README.md) from `ai-tools-base` and can be converted to any AI framework (FastMCP, LangChain, LangGraph, etc.) using companion packages.

## Installation

```bash
uv add ai-tools-github
```

## GitHub Instances

A pre-configured CodeCraft GitHub instance is available:

| Instance | URL | Factory Function |
|----------|-----|------------------|
| CodeCraft | `https://cc-github.bmwgroup.net` | `get_cc_github_instance()` |

```python
from ai_tools_github.instance import get_cc_github_instance

github = get_cc_github_instance(token="your-token")
```

## Available Tools

| Tool | Description |
|------|-------------|
| `tool_get_pull_request` | Get information about a pull request |
| `tool_get_pull_request_diff` | Get the diff from a pull request |
| `tool_get_commit_diff` | Get the diff for a specific commit |
| `tool_batch_analyze_pull_request` | Analyze multiple PRs against an objective |
| `tool_get_pull_requests_between_commits` | Find PRs merged between two commits |
| `tool_search_pull_requests` | Search for pull requests |
| `tool_get_issues_history` | Get issue history for a repository |
| `tool_get_repo_history` | Get commit history for a repository |
| `tool_get_repo_stats` | Get repository statistics |
| `tool_get_repo_tree` | Get repository file tree |
| `tool_get_file_content` | Get file content from a repository |
| `tool_add_comment_to_pull_request` | Add a comment to a pull request |
| `tool_add_label_to_pull_request` | Add a label to a pull request |
| `tool_remove_label_from_pull_request` | Remove a label from a pull request |

## Example

```python
from ai_tools_github import tool_get_pull_request_diff
from ai_tools_github.instance import get_cc_github_instance
from ai_tools_to_mcp import to_mcp_tool

github = get_cc_github_instance(token="your-token")

# Convert to MCP tool
mcp_tool = to_mcp_tool(
    tool_get_pull_request_diff,
    constants={"github": github}
)
```

### Batch Analysis

Analyze multiple pull requests against a specific objective:

```python
from ai_tools_github import tool_batch_analyze_pull_request
from ai_tools_to_langgraph import to_langgraph_tool

langgraph_tool = to_langgraph_tool(
    tool_batch_analyze_pull_request,
    constants={"github": github}
)

# Find PRs related to a specific error
result = langgraph_tool._run(
    pull_requests=[
        {"owner": "org", "repo": "backend", "number": 42},
        {"owner": "org", "repo": "frontend", "number": 17}
    ],
    analysis_objective="Find changes related to authentication errors"
)
```

### Find PRs Between Commits

Useful for root cause analysis:

```python
from ai_tools_github.pull_requests_between_commits import get_pull_requests_between_commits

prs = get_pull_requests_between_commits(
    owner="org",
    repo="repo",
    branch="main",
    start_commit_hash="abc123",
    end_commit_hash="def456",
    github=github
)
```

## Related Packages

- **ai-tools-base** – Framework-agnostic tool definitions
- **ai-tools-zuul-root-cause** – Root cause analysis using GitHub and Zuul
- **ai-tools-to-mcp** – Convert tools to FastMCP format
- **ai-tools-to-langgraph** – Convert tools to LangChain format
