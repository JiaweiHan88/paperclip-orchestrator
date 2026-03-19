# @paperclipai/plugin-figma

Paperclip connector plugin for **Figma**.

## Capabilities

- Link Figma designs (files, frames, components) to Paperclip issues
- Track file version history and surface design previews
- Inbound Figma webhooks for file_update and comment events
- Scheduled polling as a fallback
- Dashboard widget showing design sync status
- Issue and project detail tabs with design links
- Agent tools for querying Figma context during runs (coming soon)

## Install (local dev)

```sh
pnpm --filter @paperclipai/plugin-figma build
pnpm paperclipai plugin install ./packages/plugins/examples/plugin-figma
```

## Configuration

Set the following in plugin settings:

| Setting | Description |
|---------|-------------|
| Figma Access Token | Secret ref for PAT or OAuth token |
| Figma Team ID | Team whose files should be tracked |
| Webhook Passcode | Secret ref for webhook verification |
| Sync Interval | Polling frequency in minutes (default: 15) |

## Status

Skeleton — sync logic and agent tools are not yet implemented.
