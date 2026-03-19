# @paperclipai/plugin-github

Paperclip connector plugin for **GitHub**.

## Capabilities

- Bidirectional issue and comment sync between Paperclip and GitHub Issues
- Pull request linking to Paperclip issues
- Inbound GitHub webhooks for real-time updates
- Scheduled polling as a fallback sync mechanism
- Dashboard widget showing sync health
- Issue and project detail tabs linking to GitHub
- Agent tools for querying GitHub during runs (coming soon)

## Install (local dev)

```sh
pnpm --filter @paperclipai/plugin-github build
pnpm paperclipai plugin install ./packages/plugins/examples/plugin-github
```

## Configuration

Set the following in plugin settings:

| Setting | Description |
|---------|-------------|
| GitHub Token | Secret ref for PAT or GitHub App installation token |
| GitHub API Base URL | `https://api.github.com` or your GHES URL |
| Repo Mappings | JSON mapping of Paperclip project IDs → `owner/repo` |
| Sync Interval | Polling frequency in minutes (default: 5) |
| Webhook Secret | Secret ref for signature verification |

## Status

Skeleton — sync logic and agent tools are not yet implemented.
