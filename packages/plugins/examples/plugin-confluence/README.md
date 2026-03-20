# @paperclipai/plugin-confluence

Paperclip connector plugin for **Atlassian Confluence**.

## Capabilities

- Link Confluence knowledge base pages to Paperclip issues and projects
- Index page content so agents can retrieve documentation context during runs
- Inbound Confluence webhooks for page and comment events
- Scheduled polling as a fallback
- Dashboard widget showing index health
- Issue and project detail tabs with linked pages
- **12 agent tools** for searching and reading/writing Confluence (via AI Tools Bridge)

## Agent Tools

Tools are automatically registered when the plugin starts and the AI Tools Bridge is reachable.

| Tool | Risk | Description |
|------|------|-------------|
| `get_confluence_page_by_id` | LOW | Fetch a Confluence page by ID (markdown) |
| `get_confluence_page_by_title` | LOW | Fetch a Confluence page by title and space key |
| `get_confluence_page_by_id_html` | LOW | Fetch raw HTML storage format of a page by ID |
| `get_confluence_page_by_title_html` | LOW | Fetch raw HTML storage format of a page by title |
| `search_confluence_with_cql` | LOW | Search using CQL (Confluence Query Language) |
| `search_confluence_pages_freetext` | LOW | Search pages using free-text query |
| `get_confluence_spaces` | LOW | List all accessible Confluence spaces |
| `get_confluence_page_tree` | LOW | Get the hierarchical page tree for a space or page |
| `create_confluence_page` | MEDIUM | Create a new page in a specified space |
| `add_confluence_comment` | MEDIUM | Add a comment to an existing page |
| `update_confluence_page` | HIGH | Update an existing page with new content |
| `relocate_confluence_page` | HIGH | Move or copy a page to a different parent |

Risk levels map to the Paperclip governance model: HIGH tools require an approval gate when company governance is enabled.

## Install (local dev)

```sh
pnpm --filter @paperclipai/plugin-confluence build
pnpm paperclipai plugin install ./packages/plugins/examples/plugin-confluence
```

## Configuration

Set the following in plugin settings:

| Setting | Key | Description |
|---------|-----|-------------|
| Confluence Base URL | `confluenceBaseUrl` | e.g. `https://yourteam.atlassian.net/wiki` |
| Confluence API Token (secret ref) | `confluenceTokenSecretRef` | Secret reference for a Confluence PAT |
| Confluence User Email | `confluenceUserEmail` | Email for basic-auth with the API token |
| Space Keys | `spaceKeys` | Comma-separated Confluence space keys to index |
| Sync Interval (minutes) | `syncIntervalMinutes` | Polling frequency (default: 15) |

The `AI_TOOLS_BRIDGE_URL` environment variable must be set on the Paperclip server for agent tools to work (default: `http://ai-tools-bridge:8000`). See `doc/DEVELOPING.md` for setup instructions.

