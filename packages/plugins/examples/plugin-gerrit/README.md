# @paperclipai/plugin-gerrit

Paperclip connector plugin for **Gerrit Code Review**.

## Capabilities

- Link Paperclip issues to Gerrit changes
- Track review scores, comments, and merge status
- Inbound webhook for Gerrit stream-events
- Scheduled polling as a fallback sync mechanism
- Dashboard widget showing review health
- Issue and project detail tabs linking to Gerrit changes
- **25 agent tools** for querying and managing Gerrit changes during agent runs (via AI Tools Bridge)

## Agent Tools

Tools are automatically registered when the plugin starts and the AI Tools Bridge is reachable.

| Tool | Risk | Description |
|------|------|-------------|
| `query_changes` | LOW | Query Gerrit changes using a search query |
| `query_changes_by_date` | LOW | Query changes filtered by date range |
| `get_most_recent_cl` | LOW | Get the most recent change for a project/branch |
| `get_change_details` | LOW | Fetch full details for a specific change |
| `changes_submitted_together` | LOW | List changes submitted together with a given CL |
| `list_change_comments` | LOW | List all comments on a change |
| `get_commit_message` | LOW | Get the commit message for a change |
| `get_bugs_from_cl` | LOW | Extract bug/issue references from a CL |
| `get_file_content` | LOW | Read file content at a specific patchset |
| `list_change_files` | LOW | List files modified in a change |
| `get_change_diff` | LOW | Get the full diff for a change |
| `get_file_diff` | LOW | Get the diff for a specific file in a change |
| `get_project_branches` | LOW | List branches for a Gerrit project |
| `suggest_reviewers` | LOW | Suggest reviewers for a change |
| `add_reviewer` | MEDIUM | Add a reviewer to a change |
| `post_review_comment` | MEDIUM | Post an inline or top-level review comment |
| `set_ready_for_review` | MEDIUM | Mark a change as ready for review |
| `set_work_in_progress` | MEDIUM | Mark a change as work-in-progress |
| `set_topic` | MEDIUM | Set the topic on a change |
| `create_change` | HIGH | Create a new Gerrit change |
| `abandon_change` | HIGH | Abandon an existing change |
| `revert_change` | HIGH | Revert a submitted change |
| `revert_submission` | HIGH | Revert an entire submission |
| `set_review` | HIGH | Submit a review vote (Code-Review, Verified, etc.) |

Risk levels map to the Paperclip governance model: HIGH tools require an approval gate when company governance is enabled.

## Install (local dev)

```sh
pnpm --filter @paperclipai/plugin-gerrit build
pnpm paperclipai plugin install ./packages/plugins/examples/plugin-gerrit
```

## Configuration

Set the following in plugin settings:

| Setting | Key | Description |
|---------|-----|-------------|
| Gerrit Base URL | `gerritBaseUrl` | e.g. `https://gerrit.example.com` |
| Gerrit API Token (secret ref) | `gerritTokenSecretRef` | Secret reference for a Gerrit HTTP password |
| Gerrit Username | `gerritUsername` | Username for Gerrit HTTP authentication |
| Sync Interval (minutes) | `syncIntervalMinutes` | Polling frequency (default: 15) |
| Project Mappings | `projectMappings` | JSON mapping of Gerrit projects to Paperclip projects |

The `AI_TOOLS_BRIDGE_URL` environment variable must be set on the Paperclip server for agent tools to work (default: `http://ai-tools-bridge:8000`). See `doc/DEVELOPING.md` for setup instructions.
