# @paperclipai/plugin-confluence

Paperclip connector plugin for **Atlassian Confluence**.

## Capabilities

- Link Confluence knowledge base pages to Paperclip issues and projects
- Index page content so agents can retrieve documentation context during runs
- Inbound Confluence webhooks for page and comment events
- Scheduled polling as a fallback
- Dashboard widget showing index health
- Issue and project detail tabs with linked pages
- Agent tools for searching and reading Confluence (coming soon)

## Install (local dev)

```sh
pnpm --filter @paperclipai/plugin-confluence build
pnpm paperclipai plugin install ./packages/plugins/examples/plugin-confluence
```

## Configuration

Set the following in plugin settings:

| Setting | Description |
|---------|-------------|
| Confluence Base URL | e.g. `https://yourteam.atlassian.net/wiki` |
| Confluence API Token | Secret ref for authentication |
| Confluence User Email | Email for basic-auth with the API token |
| Space Keys | Comma-separated list of space keys to index |
| Sync Interval | Polling frequency in minutes (default: 15) |

## Status

Skeleton — sync logic and agent tools are not yet implemented.
