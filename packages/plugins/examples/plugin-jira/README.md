# @paperclipai/plugin-jira

Paperclip connector plugin for **Atlassian Jira**.

## Capabilities

- Bidirectional issue and comment sync between Paperclip and Jira
- Inbound Jira webhooks for real-time updates
- Scheduled polling as a fallback sync mechanism
- Dashboard widget showing sync health
- Issue and project detail tabs linking to Jira
- **11 agent tools** for querying and mutating Jira during agent runs (via AI Tools Bridge)

## Agent Tools

Tools are automatically registered when the plugin starts and the AI Tools Bridge is reachable.

| Tool | Risk | Description |
|------|------|-------------|
| `get_jira_issue` | LOW | Fetch details of a Jira issue by key |
| `download_jira_attachment` | LOW | Download an attachment from a Jira issue |
| `search_jira` | LOW | Search Jira issues using JQL |
| `get_jira_pull_requests` | LOW | Get pull requests associated with a Jira issue |
| `get_jira_fields` | LOW | Discover available fields for a project or issue type |
| `get_jira_transitions` | LOW | Get available workflow transitions for an issue |
| `create_jira_ticket` | MEDIUM | Create a new Jira ticket |
| `add_jira_comment` | MEDIUM | Add a comment to an existing Jira ticket |
| `transition_jira_issue` | MEDIUM | Transition a Jira issue to a new status |
| `link_jira_issues` | MEDIUM | Create a link between two Jira issues |
| `update_jira_ticket` | HIGH | Update an existing Jira ticket with new field values |

Risk levels map to the Paperclip governance model: HIGH tools require an approval gate when company governance is enabled.

## Install (local dev)

```sh
pnpm --filter @paperclipai/plugin-jira build
pnpm paperclipai plugin install ./packages/plugins/examples/plugin-jira
```

## Configuration

Set the following in plugin settings:

| Setting | Key | Description |
|---------|-----|-------------|
| Jira Base URL | `jiraBaseUrl` | e.g. `https://yourteam.atlassian.net` |
| Jira API Token (secret ref) | `jiraTokenSecretRef` | Secret reference for the Jira API token or PAT |
| Jira User Email | `jiraUserEmail` | Email for basic-auth with the API token |
| Sync Interval (minutes) | `syncIntervalMinutes` | Polling frequency (default: 5) |
| Project Mappings | `projectMappings` | JSON mapping of Paperclip project IDs → Jira project keys |

The `AI_TOOLS_BRIDGE_URL` environment variable must be set on the Paperclip server for agent tools to work (default: `http://ai-tools-bridge:8000`). See `doc/DEVELOPING.md` for setup instructions.

