# AI Tools Confluence

AI tools for Confluence operations and content management, providing ready-to-use tools for BMW CodeCraft and ATC Confluence instances with both read and write capabilities.

## Overview

This package provides tools for interacting with Atlassian Confluence instances, including both read and write operations. Tools are defined using the framework-agnostic [`ToolDescription`](../ai_tools_base/README.md) from `ai-tools-base` and can be converted to any AI framework (FastMCP, LangChain, LangGraph, etc.) using companion packages.

**Available Operations:**
- **Read Operations** (RiskLevel.LOW): Search pages, retrieve content, browse spaces
- **Write Operations** (RiskLevel.MEDIUM/HIGH): Create pages, update content, add comments

## Installation

```bash
uv add ai-tools-confluence
```

## Confluence Instances

Two pre-configured Confluence instances are available:

| Instance | URL | Factory Function |
|----------|-----|------------------|
| CodeCraft | `https://confluence.cc.bmwgroup.net` | `get_cc_confluence()` |
| ATC | `https://atc.bmwgroup.net/confluence` | `get_atc_confluence()` |

Both instances use Personal Access Tokens (PAT) for authentication and are configured for Confluence Server/Data Center.

```python
from ai_tools_confluence import get_cc_confluence, get_atc_confluence

# CodeCraft Confluence
cc_confluence = get_cc_confluence(token="your-pat-token")

# ATC Confluence
atc_confluence = get_atc_confluence(token="your-pat-token")
```

## Available Tools

### Read Operations (RiskLevel.LOW)

#### Get Page by ID
Retrieve a Confluence page by its unique ID:
```python
from ai_tools_confluence import get_confluence_page_by_id

page_content = get_confluence_page_by_id(
    id="123456",
    confluence=confluence
)
```

#### Get Page by Title
Retrieve a Confluence page by title and space:
```python
from ai_tools_confluence import get_confluence_page_by_title

page_content = get_confluence_page_by_title(
    title="API Documentation",
    space_key="DEV",
    confluence=confluence
)
```

#### Search with CQL
Search using Confluence Query Language:
```python
from ai_tools_confluence import search_confluence_with_cql

results = search_confluence_with_cql(
    cql_query='text ~ "release notes" AND type=page',
    confluence=confluence,
    limit=25
)
```

#### Free-text Search
Search pages using free-text queries:
```python
from ai_tools_confluence import search_confluence_pages_freetext

results = search_confluence_pages_freetext(
    text="API documentation",
    confluence=confluence,
    space_keys=["DEV", "PROD"]
)
```

#### List Spaces
Get all available Confluence spaces:
```python
from ai_tools_confluence import get_confluence_spaces

spaces = get_confluence_spaces(
    confluence=confluence,
    limit=100
)
```

#### Get Page Tree
Get hierarchical page structure for a space:
```python
from ai_tools_confluence import get_confluence_page_tree

tree = get_confluence_page_tree(
    space_key="DEV",
    confluence=confluence,
    root_page_id="123456"  # Optional
)
```

### Write Operations

#### Move Page (RiskLevel.HIGH)
Move a Confluence page to a different parent page:
```python
from ai_tools_confluence import move_confluence_page

result = move_confluence_page(
    page_id="123456",
    new_parent_id="789012",
    confluence=confluence
)
# Returns: "Successfully moved page 'My Page' (ID: 123456) to parent 'Parent Page' (ID: 789012)"
```

**Risk Level: HIGH** - This operation modifies existing content structure. The page and all its children will be moved to the new parent location.

#### Copy Page (RiskLevel.MEDIUM)
Copy a Confluence page to a different parent page:
```python
from ai_tools_confluence import copy_confluence_page

# Copy with automatic title
result = copy_confluence_page(
    page_id="123456",
    new_parent_id="789012",
    confluence=confluence
)
# Creates page with title "Original Title (Copy)"

# Copy with custom title
result = copy_confluence_page(
    page_id="123456",
    new_parent_id="789012",
    confluence=confluence,
    new_title="My Custom Copy Title"
)
# Returns: "Successfully copied page 'Original' to 'My Custom Copy Title' (ID: 999999) under parent 'Parent Page' (ID: 789012)"
```

**Risk Level: MEDIUM** - This operation creates new content. Only the single page is copied (child pages are not recursively copied).

## Example

### Reading Content

```python
from ai_tools_confluence import (
    get_cc_confluence,
    get_confluence_page_by_id,
    get_confluence_page_by_id_html,
    search_confluence_pages_freetext,
    copy_confluence_page
)

confluence = get_cc_confluence(token="your-token")

# Get page as markdown for AI analysis
markdown_content = get_confluence_page_by_id(
    id="123456",
    confluence=confluence
)
print(markdown_content)  # Clean markdown without Confluence markup

# Get page as HTML for editing while preserving formatting
html_content = get_confluence_page_by_id_html(
    id="123456",
    confluence=confluence
)
print(html_content)  # Raw HTML with Confluence macros and formatting

# Free-text search across Confluence
results = search_confluence_pages_freetext(
    text="release notes",
    confluence=confluence,
    space_keys=["DEV"]
)

# Copy a page to archive space
result = copy_confluence_page(
    page_id="123456",
    new_parent_id="archive_parent_id",
    confluence=confluence,
    new_title="Archived Release Notes"
)
```

### Writing and Editing Content

```python
from ai_tools_confluence import (
    get_cc_confluence,
    create_confluence_page,
    update_confluence_page,
    add_confluence_comment,
)

confluence = get_cc_confluence(token="your-token")

# Create a new page
result = create_confluence_page(
    space_key="PROJ",
    title="New Documentation",
    content="<p>Initial content in HTML format</p>",
    parent_id="123456",  # Optional: create as child page
    confluence=confluence,
)

# Update an existing page
result = update_confluence_page(
    page_id="789012",
    content="<p>Updated content</p>",
    title="Updated Title",  # Optional: change title
    confluence=confluence,
)

# Add a comment to a page
result = add_confluence_comment(
    page_id="789012",
    comment="<p>Great documentation! Note: ...</p>",
    confluence=confluence,
)
```

## Available Tools

### Read Operations (RiskLevel.LOW)

#### Markdown Format (for AI Processing and Analysis)
- **`get_confluence_page_by_id`** – Retrieve page content by page ID and convert to markdown
- **`get_confluence_page_by_title`** – Retrieve page content by title and space key

#### HTML Format (for Direct Page Editing)
- **`get_confluence_page_by_id_html`** – Retrieve page content by page ID in HTML storage format
- **`get_confluence_page_by_title_html`** – Retrieve page content by title and space key in HTML storage format

**Use Case Guidance:**
- **Use Markdown tools** when you need to analyze, summarize, or extract information from pages. The markdown format is optimized for AI processing and removes Confluence-specific markup.
- **Use HTML tools** when you need to edit or update pages while preserving exact Confluence formatting, macros (like info panels, TOC, etc.), and structure. The HTML storage format contains all Confluence-specific markup needed for accurate updates.

#### Search and Navigation
- **`search_confluence_with_cql`** – Search using Confluence Query Language (CQL)
- **`search_confluence_pages_freetext`** – Free-text search with optional space filtering
- **`get_confluence_spaces`** – List all spaces with keys, titles, and descriptions
- **`get_confluence_page_tree`** – Get hierarchical page tree structure for a space

### Write Operations

- **`update_confluence_page`** (RiskLevel.HIGH) – Update existing page content and/or title
  - Automatically handles version management
  - Can update content only or both content and title
  
- **`create_confluence_page`** (RiskLevel.MEDIUM) – Create new page in a space
  - Supports optional parent page for hierarchical structure
  - Returns page ID and URL for reference
  
- **`add_confluence_comment`** (RiskLevel.MEDIUM) – Add comment to existing page
  - Supports both plain text and HTML formatted comments

**Note:** All write operations use Confluence storage format (HTML) for content. The content should be properly formatted HTML that follows Confluence's storage format syntax.

## Related Packages

- **ai-tools-base** – Framework-agnostic tool definitions
- **ai-tools-to-mcp** – Convert tools to FastMCP format
- **ai-tools-to-langgraph** – Convert tools to LangChain format

