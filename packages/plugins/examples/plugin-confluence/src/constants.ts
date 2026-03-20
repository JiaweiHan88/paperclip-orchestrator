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
  // ── Read-only (LOW risk) ─────────────────────────────────────────────────
  getConfluencePageById: "get_confluence_page_by_id",
  getConfluencePageByTitle: "get_confluence_page_by_title",
  getConfluencePageByIdHtml: "get_confluence_page_by_id_html",
  getConfluencePageByTitleHtml: "get_confluence_page_by_title_html",
  searchConfluenceWithCql: "search_confluence_with_cql",
  searchConfluencePagesFreetext: "search_confluence_pages_freetext",
  getConfluenceSpaces: "get_confluence_spaces",
  getConfluencePageTree: "get_confluence_page_tree",
  // ── Medium risk ──────────────────────────────────────────────────────────
  createConfluencePage: "create_confluence_page",
  addConfluenceComment: "add_confluence_comment",
  // ── High risk ────────────────────────────────────────────────────────────
  updateConfluencePage: "update_confluence_page",
  relocateConfluencePage: "relocate_confluence_page",
} as const;
