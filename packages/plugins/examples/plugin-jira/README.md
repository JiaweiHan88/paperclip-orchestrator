# @paperclipai/plugin-jira

Paperclip connector plugin for **Atlassian Jira**.

## Capabilities

- Bidirectional issue and comment sync between Paperclip and Jira
- Inbound Jira webhooks for real-time updates
- Scheduled polling as a fallback sync mechanism
- Dashboard widget showing sync health
- Issue and project detail tabs linking to Jira
- Agent tools for querying Jira during runs (coming soon)

## Install (local dev)

```sh
pnpm --filter @paperclipai/plugin-jira build
pnpm paperclipai plugin install ./packages/plugins/examples/plugin-jira
```

## Configuration

Set the following in plugin settings:

| Setting | Description |
|---------|-------------|
| Jira Base URL | e.g. `https://yourteam.atlassian.net` |
| Jira API Token | Secret ref for authentication |
| Jira User Email | Email for basic-auth with the API token |
| Sync Interval | Polling frequency in minutes (default: 5) |
| Project Mappings | JSON mapping of Paperclip project IDs → Jira project keys |

## Status

Skeleton — sync logic and agent tools are not yet implemented.
