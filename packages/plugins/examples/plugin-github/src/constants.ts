export const PLUGIN_ID = "paperclip.github";
export const PLUGIN_VERSION = "0.1.0";
export const PAGE_ROUTE = "github";

export const SLOT_IDS = {
  page: "github-page",
  settingsPage: "github-settings-page",
  dashboardWidget: "github-dashboard-widget",
  sidebar: "github-sidebar-link",
  issueTab: "github-issue-tab",
  projectTab: "github-project-tab",
} as const;

export const EXPORT_NAMES = {
  page: "GitHubPage",
  settingsPage: "GitHubSettingsPage",
  dashboardWidget: "GitHubDashboardWidget",
  sidebar: "GitHubSidebarLink",
  issueTab: "GitHubIssueTab",
  projectTab: "GitHubProjectTab",
} as const;

export const JOB_KEYS = {
  sync: "github-sync",
} as const;

export const WEBHOOK_KEYS = {
  inbound: "github-inbound",
} as const;

export const TOOL_NAMES = {
  // ── Read-only (LOW risk) ─────────────────────────────────────────────────
  getPullRequestDiff: "get_pull_request_diff",
  getCommitDiff: "get_commit_diff",
  batchAnalyzePullRequest: "batch_analyze_pull_request",
  getPullRequestsBetweenCommits: "get_pull_requests_between_commits",
  getPullRequest: "get_pull_request",
  searchPullRequests: "search_pull_requests",
  getIssueTimeLine: "get_issue_time_line",
  getIssuesFromProjectBoard: "get_issues_from_project_board",
  getProjectFields: "get_project_fields",
  getRepoHistory: "get_repo_history",
  getRepoStats: "get_repo_stats",
  getRepoTree: "get_repo_tree",
  getFileContent: "get_file_content",
  getZuulBuildsetsForPr: "get_zuul_buildsets_for_pr",
  getPullRequestStructured: "get_pull_request_structured",
  getPullRequestState: "get_pull_request_state",
  getRepoFolderFilesPath: "get_repo_folder_files_path",
  searchCode: "search_code",
  // ── Medium risk ──────────────────────────────────────────────────────────
  addCommentToPullRequest: "add_comment_to_pull_request",
  addLabelToPullRequest: "add_label_to_pull_request",
  removeLabelFromPullRequest: "remove_label_from_pull_request",
  createReactionToPullRequestComment: "create_reaction_to_pull_request_comment",
  // ── High risk ────────────────────────────────────────────────────────────
  updatePullRequestDescription: "update_pull_request_description",
  injectToPullRequestDescription: "inject_to_pull_request_description",
  createBranch: "create_branch",
  createCommitOnBranch: "create_commit_on_branch",
  createPullRequest: "create_pull_request",
  createIssue: "create_issue",
} as const;
