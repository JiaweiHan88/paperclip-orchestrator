export const PLUGIN_ID = "paperclip.figma";
export const PLUGIN_VERSION = "0.1.0";
export const PAGE_ROUTE = "figma";

export const SLOT_IDS = {
  page: "figma-page",
  settingsPage: "figma-settings-page",
  dashboardWidget: "figma-dashboard-widget",
  sidebar: "figma-sidebar-link",
  issueTab: "figma-issue-tab",
  projectTab: "figma-project-tab",
} as const;

export const EXPORT_NAMES = {
  page: "FigmaPage",
  settingsPage: "FigmaSettingsPage",
  dashboardWidget: "FigmaDashboardWidget",
  sidebar: "FigmaSidebarLink",
  issueTab: "FigmaIssueTab",
  projectTab: "FigmaProjectTab",
} as const;

export const JOB_KEYS = {
  sync: "figma-sync",
} as const;

export const WEBHOOK_KEYS = {
  inbound: "figma-inbound",
} as const;

export const TOOL_NAMES = {
  // Tools will be defined in a future pass.
} as const;
