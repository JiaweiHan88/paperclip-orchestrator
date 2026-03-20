export const PLUGIN_ID = "paperclip.gerrit";
export const PLUGIN_VERSION = "0.1.0";
export const PAGE_ROUTE = "gerrit";

export const SLOT_IDS = {
  page: "gerrit-page",
  settingsPage: "gerrit-settings-page",
  dashboardWidget: "gerrit-dashboard-widget",
  sidebar: "gerrit-sidebar-link",
  issueTab: "gerrit-issue-tab",
  projectTab: "gerrit-project-tab",
} as const;

export const EXPORT_NAMES = {
  page: "GerritPage",
  settingsPage: "GerritSettingsPage",
  dashboardWidget: "GerritDashboardWidget",
  sidebar: "GerritSidebarLink",
  issueTab: "GerritIssueTab",
  projectTab: "GerritProjectTab",
} as const;

export const JOB_KEYS = {
  sync: "gerrit-sync",
} as const;

export const WEBHOOK_KEYS = {
  streamEvents: "gerrit-stream-events",
} as const;

export const TOOL_NAMES = {
  // ── Read-only (LOW risk) ─────────────────────────────────────────────────
  queryChanges: "query_changes",
  queryChangesByDate: "query_changes_by_date",
  getMostRecentCl: "get_most_recent_cl",
  getChangeDetails: "get_change_details",
  changesSubmittedTogether: "changes_submitted_together",
  listChangeComments: "list_change_comments",
  getCommitMessage: "get_commit_message",
  getBugsFromCl: "get_bugs_from_cl",
  getFileContent: "get_file_content",
  listChangeFiles: "list_change_files",
  getChangeDiff: "get_change_diff",
  getFileDiff: "get_file_diff",
  getProjectBranches: "get_project_branches",
  suggestReviewers: "suggest_reviewers",
  // ── Medium risk ──────────────────────────────────────────────────────────
  addReviewer: "add_reviewer",
  postReviewComment: "post_review_comment",
  setReadyForReview: "set_ready_for_review",
  setWorkInProgress: "set_work_in_progress",
  setTopic: "set_topic",
  // ── High risk ────────────────────────────────────────────────────────────
  createChange: "create_change",
  abandonChange: "abandon_change",
  revertChange: "revert_change",
  revertSubmission: "revert_submission",
  setReview: "set_review",
} as const;
