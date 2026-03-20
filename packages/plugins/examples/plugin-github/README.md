# @paperclipai/plugin-github

Paperclip connector plugin for **GitHub**.

## Capabilities

- Bidirectional issue and comment sync between Paperclip and GitHub Issues
- Pull request linking to Paperclip issues
- Inbound GitHub webhooks for real-time updates
- Scheduled polling as a fallback sync mechanism
- Dashboard widget showing sync health
- Issue and project detail tabs linking to GitHub
- **28 agent tools** for querying and mutating GitHub during agent runs (via AI Tools Bridge)

## Agent Tools

Tools are automatically registered when the plugin starts and the AI Tools Bridge is reachable.

| Tool | Risk | Description |
|------|------|-------------|
| `get_pull_request_diff` | LOW | Get the diff for a pull request |
| `get_commit_diff` | LOW | Get the diff for a commit |
| `batch_analyze_pull_request` | LOW | Analyze multiple PRs for relationships and patterns |
| `get_pull_requests_between_commits` | LOW | List PRs between two commits |
| `get_pull_request` | LOW | Get pull request details |
| `search_pull_requests` | LOW | Search pull requests in a repository |
| `get_issue_time_line` | LOW | Get the event timeline for a GitHub issue |
| `get_issues_from_project_board` | LOW | List filtered issues from a GitHub project board |
| `get_project_fields` | LOW | Get field definitions for a GitHub project |
| `get_repo_history` | LOW | Get commit history for a repository |
| `get_repo_stats` | LOW | Get statistics for a repository |
| `get_repo_tree` | LOW | Get the file tree for a repository |
| `get_file_content` | LOW | Read a file from a repository |
| `get_zuul_buildsets_for_pr` | LOW | Get Zuul CI buildsets for a pull request |
| `get_pull_request_structured` | LOW | Get structured pull request data |
| `get_pull_request_state` | LOW | Get the current status of a pull request |
| `get_repo_folder_files_path` | LOW | List files in a repository folder |
| `search_code` | LOW | Search code across repositories |
| `add_comment_to_pull_request` | MEDIUM | Post a comment on a pull request |
| `add_label_to_pull_request` | MEDIUM | Add a label to a pull request |
| `remove_label_from_pull_request` | MEDIUM | Remove a label from a pull request |
| `create_reaction_to_pull_request_comment` | MEDIUM | Add a reaction to a PR comment |
| `update_pull_request_description` | HIGH | Replace the description of a pull request |
| `inject_to_pull_request_description` | HIGH | Append a section to a pull request description |
| `create_branch` | HIGH | Create a new branch in a repository |
| `create_commit_on_branch` | HIGH | Commit files to an existing branch |
| `create_pull_request` | HIGH | Open a new pull request |
| `create_issue` | HIGH | Create a new GitHub issue |

Risk levels map to the Paperclip governance model: HIGH tools require an approval gate when company governance is enabled.

## Install (local dev)

```sh
pnpm --filter @paperclipai/plugin-github build
pnpm paperclipai plugin install ./packages/plugins/examples/plugin-github
```

## Configuration

Set the following in plugin settings:

| Setting | Key | Description |
|---------|-----|-------------|
| GitHub Token (secret ref) | `githubTokenSecretRef` | Secret reference for a PAT or GitHub App installation token |
| GitHub API Base URL | `githubApiBaseUrl` | `https://api.github.com` or your GHES URL |
| Repo Mappings | `repoMappings` | JSON mapping of Paperclip project IDs → `owner/repo` |
| Sync Interval (minutes) | `syncIntervalMinutes` | Polling frequency (default: 5) |
| Webhook Secret (secret ref) | `webhookSecret` | Secret reference for GitHub webhook signature verification |

The `AI_TOOLS_BRIDGE_URL` environment variable must be set on the Paperclip server for agent tools to work (default: `http://ai-tools-bridge:8000`). See `doc/DEVELOPING.md` for setup instructions.

