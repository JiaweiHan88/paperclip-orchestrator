# AI Tools JIRA

AI tools for JIRA project management and issue tracking integration, providing comprehensive functionality for issue creation, management, and search.

## Overview

This package provides tools for interacting with Atlassian JIRA instances. Tools are defined using the framework-agnostic [`ToolDescription`](../ai_tools_base/README.md) from `ai-tools-base` and can be converted to any AI framework (FastMCP, LangChain, LangGraph, etc.) using companion packages.

## Installation

```bash
uv add ai-tools-jira
```

## JIRA Instances

Two pre-configured JIRA instances are available:

| Instance | URL | Factory Function |
|----------|-----|------------------|
| CodeCraft | `https://jira.cc.bmwgroup.net` | `get_cc_jira_instance()` |
| ATC | `https://atc.bmwgroup.net/jira/` | `ATCJira()` |

Both instances use Personal Access Tokens (PAT) for authentication.

```python
from ai_tools_jira import get_cc_jira_instance

jira = get_cc_jira_instance(token="your-pat-token")
```

## Available Tools

| Tool | Description |
|------|-------------|
| `tool_get_jira_issue` | Fetch and format details of a JIRA issue |
| `tool_search_jira` | Search JIRA using JQL queries |
| `tool_create_jira_ticket` | Create new JIRA tickets |
| `tool_update_jira_ticket` | Update existing JIRA tickets |
| `tool_add_jira_comment` | Add comments to JIRA issues |
| `tool_link_jira_issues` | Create bidirectional links between JIRA issues |
| `tool_download_jira_attachment` | Download attachments from JIRA issues |
| `tool_get_jira_pull_requests` | Get pull requests linked and mentioned in a JIRA issue |
| `tool_get_jira_transitions` | Get available status transitions for a JIRA issue |
| `tool_transition_jira_issue` | Transition a JIRA issue to a new status |

## Example

```python
from ai_tools_jira import get_cc_jira_instance, tool_get_jira_issue
from ai_tools_to_mcp import to_mcp_tool

jira = get_cc_jira_instance(token="your-token")

# Convert to MCP tool
mcp_tool = to_mcp_tool(
    tool_get_jira_issue,
    constants={"jira_instance": jira}
)

# Or use directly
from ai_tools_jira.issue import get_jira_issue

issue_markdown = get_jira_issue(
    key="PROJECT-123",
    jira_instance=jira
)
```

## Markdown Support

All text inputs (descriptions, comments) are automatically converted from markdown to JIRA wiki markup format. This allows you to use familiar markdown syntax which will be properly displayed in JIRA.

### Supported Markdown Syntax

| Markdown       | JIRA Wiki Markup   | Description     |
| -------------- | ------------------ | --------------- |
| `# Header`     | `h1. Header`       | Headers (h1-h6) |
| `**bold**`     | `*bold*`           | Bold text       |
| `*italic*`     | `_italic_`         | Italic text     |
| `- item`       | `* item`           | Bullet lists    |
| `  - nested`   | `** nested`        | Nested bullets  |
| `1. item`      | `# item`           | Numbered lists  |
| `` `code` ``   | `{{code}}`         | Inline code     |
| ` ```code``` ` | `{code}code{code}` | Code blocks     |

### Example

```python
from ai_tools_jira.create_ticket import create_jira_ticket

# Create ticket with markdown description
create_jira_ticket(
    project_key="PROJ",
    issue_type="Story",
    summary="New Feature",
    description="""
## Problem Description
The system needs **improved performance**.

## Solution
- Optimize queries
- Add caching layer
  - Redis for session data
  - Memcached for API responses

## Implementation
1. Set up Redis cluster
2. Update application code
3. Add monitoring

Use the `cache_key()` function for all cache operations.
""",
    jira_instance=jira
)
# The markdown will be automatically converted to proper JIRA formatting
```

## Features

### Issue Retrieval

Fetches detailed issue information and renders it as markdown, including:

- Basic fields: Key, Status, Assignee, Reporter, Priority, Components
- Dates: Created, Updated
- Custom fields: Story Points, Definition of Done, Acceptance Criteria
- Attachments and Comments

```python
from ai_tools_jira.issue import get_jira_issue

result = get_jira_issue(key="SWH-456", jira_instance=jira)
```

### JQL Search

Search for issues using JIRA Query Language. The results include a header showing the total count of issues found and how many are being displayed (useful when results are paginated):

```python
from ai_tools_jira.search import search_jira

results = search_jira(
    jql="project = SWH AND status = Open",
    jira_instance=jira
)
# Returns markdown with header like: "Found 150 issues (showing 50)"
```

### Issue Management

Create, update, and comment on issues:

```python
from ai_tools_jira.create_ticket import create_jira_ticket
from ai_tools_jira.update_ticket import update_jira_ticket
from ai_tools_jira.add_comment import add_jira_comment

# Create a new ticket with optional fields
new_issue = create_jira_ticket(
    project_key="SWH",
    issue_type="Story",
    summary="New feature request",
    description="Detailed description...",
    assignee="john.doe",
    priority="High",
    components=["Backend", "API"],
    jira_instance=jira
)

# Update existing ticket
update_jira_ticket(
    issue_key="SWH-123",
    summary="Updated summary",
    components=["Frontend"],
    jira_instance=jira
)
    jira_instance=jira
)

# Add a comment
add_jira_comment(
    key="SWH-123",
    comment="This is a new comment",
    jira_instance=jira
)
```

### Issue Linking

Create relationships between issues:

```python
from ai_tools_jira.link_issues import link_jira_issues

# Link issues with a "causes" relationship
link_jira_issues(
    inward_issue="PROJ-100",
    outward_issue="PROJ-200",
    link_type="causes",  # Options: causes, blocks, relates, duplicates, clones
    jira_instance=jira
)
```

### Pull Request Integration

Get pull requests both linked through Git integration and mentioned in issue text:

```python
from ai_tools_jira.pull_requests import get_jira_pull_requests

prs = get_jira_pull_requests(
    issue_key="SWH-123",
    jira_instance=jira
)
```

### Issue Transitions

Get available transitions and change issue status:

```python
from ai_tools_jira.transitions import get_jira_transitions, transition_jira_issue

# Get available transitions for an issue
transitions = get_jira_transitions(
    issue_key="SWH-123",
    jira_instance=jira
)

# Transition an issue to a new status
transition_jira_issue(
    issue_key="SWH-123",
    transition_id="21",  # ID from get_jira_transitions
    jira_instance=jira,
    fields={"resolution": {"name": "Fixed"}}
)
```

## Related Packages

- **ai-tools-base** – Framework-agnostic tool definitions
- **ai-tools-to-mcp** – Convert tools to FastMCP format
- **ai-tools-to-langgraph** – Convert tools to LangChain format
