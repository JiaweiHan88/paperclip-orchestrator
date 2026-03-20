export const PLUGIN_ID = "paperclip.jira";
export const PLUGIN_VERSION = "0.1.0";
export const PAGE_ROUTE = "jira";

export const SLOT_IDS = {
  page: "jira-page",
  settingsPage: "jira-settings-page",
  dashboardWidget: "jira-dashboard-widget",
  sidebar: "jira-sidebar-link",
  issueTab: "jira-issue-tab",
  projectTab: "jira-project-tab",
} as const;

export const EXPORT_NAMES = {
  page: "JiraPage",
  settingsPage: "JiraSettingsPage",
  dashboardWidget: "JiraDashboardWidget",
  sidebar: "JiraSidebarLink",
  issueTab: "JiraIssueTab",
  projectTab: "JiraProjectTab",
} as const;

export const JOB_KEYS = {
  sync: "jira-sync",
} as const;

export const WEBHOOK_KEYS = {
  inbound: "jira-inbound",
} as const;

export const TOOL_NAMES = {
  // ── Read-only (LOW risk) ─────────────────────────────────────────────────
  getJiraIssue: "get_jira_issue",
  downloadJiraAttachment: "download_jira_attachment",
  searchJira: "search_jira",
  getJiraPullRequests: "get_jira_pull_requests",
  getJiraFields: "get_jira_fields",
  getJiraTransitions: "get_jira_transitions",
  // ── Medium risk ──────────────────────────────────────────────────────────
  createJiraTicket: "create_jira_ticket",
  addJiraComment: "add_jira_comment",
  transitionJiraIssue: "transition_jira_issue",
  linkJiraIssues: "link_jira_issues",
  // ── High risk ────────────────────────────────────────────────────────────
  updateJiraTicket: "update_jira_ticket",
} as const;
