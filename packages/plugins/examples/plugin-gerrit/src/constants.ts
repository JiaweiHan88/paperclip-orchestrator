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
  // Tools will be defined in a future pass.
} as const;
