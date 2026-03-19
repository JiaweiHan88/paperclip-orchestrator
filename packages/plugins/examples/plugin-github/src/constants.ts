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
  // Tools will be defined in a future pass.
} as const;
