# AI Tools Gerrit

AI tools for Gerrit code review operations, providing functionality for querying changes, inspecting diffs, managing reviewers, posting comments, and performing change actions.

## Overview

This package provides tools for interacting with Gerrit code review. Tools are defined using the framework-agnostic [`ToolDescription`](../ai_tools_base/README.md) from `ai-tools-base` and can be converted to any AI framework (FastMCP, LangChain, LangGraph, etc.) using companion packages.

## Installation

```bash
uv add ai-tools-gerrit
```

## Gerrit Instances

A pre-configured CodeCraft Gerrit instance is available:

| Instance | URL | Factory Function |
|----------|-----|------------------|
| CodeCraft | `https://gerrit.cc.bmwgroup.net/a` | `get_cc_gerrit_instance()` |

```python
from ai_tools_gerrit.instance import get_cc_gerrit_instance

gerrit = get_cc_gerrit_instance(username="your-username", token="your-http-password")
```

The `token` is the HTTP password generated in Gerrit under **Settings → HTTP Credentials**.

## Available Tools

### Read (LOW risk)

| Tool | Description |
|------|-------------|
| `tool_query_changes` | Search for Gerrit changes using a query string |
| `tool_query_changes_by_date` | Find changes within a date range |
| `tool_get_most_recent_cl` | Get the most recent CL for a user |
| `tool_get_change_details` | Get detailed info about a change (labels, messages, revisions) |
| `tool_changes_submitted_together` | List changes submitted together with a given CL |
| `tool_get_commit_message` | Get the commit message for a change |
| `tool_get_bugs_from_cl` | Extract bug IDs referenced in a change's commit message |
| `tool_list_change_files` | List files modified in a change (with aggregate totals and rename info) |
| `tool_get_file_diff` | Get the diff for a specific file in a change |
| `tool_get_change_diff` | Get the unified diff for an entire CL (with file scope filtering) |
| `tool_get_file_content` | Retrieve file content from a project branch |
| `tool_get_project_branches` | List branches of a project (with regex filtering) |
| `tool_list_change_comments` | List all comments on a change, grouped by file |
| `tool_suggest_reviewers` | Suggest reviewers for a change based on a search query |

### Write (MEDIUM risk)

| Tool | Description |
|------|-------------|
| `tool_add_reviewer` | Add a user or group as a reviewer or CC |
| `tool_post_review_comment` | Post an inline review comment on a specific line |
| `tool_set_ready_for_review` | Mark a change as ready for review |
| `tool_set_work_in_progress` | Mark a change as Work-In-Progress |
| `tool_set_topic` | Set or clear the topic of a change |

### Destructive (HIGH risk)

| Tool | Description |
|------|-------------|
| `tool_create_change` | Create a new empty change |
| `tool_abandon_change` | Abandon a change |
| `tool_revert_change` | Revert a submitted change, creating a new revert CL |
| `tool_revert_submission` | Revert an entire submission, creating one or more revert CLs |
| `tool_set_review` | Set review labels/votes and post review messages |

## Example

```python
from ai_tools_gerrit import tool_get_change_details
from ai_tools_gerrit.instance import get_cc_gerrit_instance
from ai_tools_to_mcp import to_mcp_tool

gerrit = get_cc_gerrit_instance(username="alice", token="your-http-password")

# Convert to MCP tool
mcp_tool = to_mcp_tool(
    tool_get_change_details,
    constants={"gerrit": gerrit}
)
```

### Query Changes

```python
from ai_tools_gerrit import tool_query_changes
from ai_tools_to_langgraph import to_langgraph_tool

langgraph_tool = to_langgraph_tool(tool_query_changes, constants={"gerrit": gerrit})

result = langgraph_tool._run(query="owner:self status:open")
```

### Extract Bug IDs

```python
from ai_tools_gerrit import tool_get_bugs_from_cl

bugs_tool = to_langgraph_tool(tool_get_bugs_from_cl, constants={"gerrit": gerrit})
result = bugs_tool._run(change_id="12345")
```

## Related Packages

- **ai-tools-base** – Framework-agnostic tool definitions
- **ai-tools-to-mcp** – Convert tools to FastMCP format
- **ai-tools-to-langgraph** – Convert tools to LangChain format
