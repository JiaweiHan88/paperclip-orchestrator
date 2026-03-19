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
  // Tools will be defined in a future pass.
} as const;
