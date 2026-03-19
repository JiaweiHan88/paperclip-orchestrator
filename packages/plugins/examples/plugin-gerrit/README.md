# @paperclipai/plugin-gerrit

Paperclip connector plugin for **Gerrit Code Review**.

## Capabilities

- Link Paperclip issues to Gerrit changes
- Track review scores, comments, and merge status
- Inbound webhook for Gerrit stream-events
- Scheduled polling as a fallback sync mechanism
- Dashboard widget showing review health
- Issue and project detail tabs linking to Gerrit changes
- Agent tools for querying Gerrit during runs (coming soon)

## Install (local dev)

```sh
pnpm --filter @paperclipai/plugin-gerrit build
pnpm paperclipai plugin install ./packages/plugins/examples/plugin-gerrit
```

## Configuration

Set the following in plugin settings:

| Setting | Description |
|---------|-------------|
| Gerrit Base URL | e.g. `https://gerrit.example.com` |
| Gerrit HTTP Credentials | Secret ref for HTTP password or access token |
| Gerrit Username | Username for HTTP authentication |
| Sync Interval | Polling frequency in minutes (default: 5) |
| Project Mappings | JSON mapping of Paperclip project IDs → Gerrit project names |

## Status

Skeleton — sync logic and agent tools are not yet implemented.
