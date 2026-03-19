export const PLUGIN_ID = "paperclip.confluence";
export const PLUGIN_VERSION = "0.1.0";
export const PAGE_ROUTE = "confluence";

export const SLOT_IDS = {
  page: "confluence-page",
  settingsPage: "confluence-settings-page",
  dashboardWidget: "confluence-dashboard-widget",
  sidebar: "confluence-sidebar-link",
  issueTab: "confluence-issue-tab",
  projectTab: "confluence-project-tab",
} as const;

export const EXPORT_NAMES = {
  page: "ConfluencePage",
  settingsPage: "ConfluenceSettingsPage",
  dashboardWidget: "ConfluenceDashboardWidget",
  sidebar: "ConfluenceSidebarLink",
  issueTab: "ConfluenceIssueTab",
  projectTab: "ConfluenceProjectTab",
} as const;

export const JOB_KEYS = {
  sync: "confluence-sync",
} as const;

export const WEBHOOK_KEYS = {
  inbound: "confluence-inbound",
} as const;

export const TOOL_NAMES = {
  // Tools will be defined in a future pass.
} as const;
