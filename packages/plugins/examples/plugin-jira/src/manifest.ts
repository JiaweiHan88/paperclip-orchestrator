import type { PaperclipPluginManifestV1 } from "@paperclipai/plugin-sdk";
import {
  EXPORT_NAMES,
  JOB_KEYS,
  PAGE_ROUTE,
  PLUGIN_ID,
  PLUGIN_VERSION,
  SLOT_IDS,
  TOOL_NAMES,
  WEBHOOK_KEYS,
} from "./constants.js";

const manifest: PaperclipPluginManifestV1 = {
  id: PLUGIN_ID,
  apiVersion: 1,
  version: PLUGIN_VERSION,
  displayName: "Jira",
  description:
    "Sync issues, comments, and status between Paperclip and Atlassian Jira. " +
    "Provides bidirectional sync via webhooks and scheduled polling, plus agent " +
    "tools for querying Jira during runs.",
  author: "Paperclip",
  categories: ["connector"],
  capabilities: [
    // Data read
    "companies.read",
    "projects.read",
    "issues.read",
    "issue.comments.read",
    "agents.read",

    // Data write
    "issues.create",
    "issues.update",
    "issue.comments.create",
    "activity.log.write",

    // Plugin state
    "plugin.state.read",
    "plugin.state.write",

    // Runtime / integration
    "events.subscribe",
    "jobs.schedule",
    "webhooks.receive",
    "http.outbound",
    "secrets.read-ref",

    // Agent tools (registered later)
    "agent.tools.register",

    // UI
    "instance.settings.register",
    "ui.sidebar.register",
    "ui.page.register",
    "ui.detailTab.register",
    "ui.dashboardWidget.register",
  ],
  entrypoints: {
    worker: "./dist/worker.js",
    ui: "./dist/ui",
  },
  instanceConfigSchema: {
    type: "object",
    properties: {
      jiraBaseUrl: {
        type: "string",
        title: "Jira Base URL",
        description: "Base URL of your Jira instance (e.g. https://yourteam.atlassian.net)",
        default: "",
      },
      jiraTokenSecretRef: {
        type: "string",
        title: "Jira API Token (secret ref)",
        description: "Secret reference for the Jira API token or PAT.",
        default: "",
      },
      jiraUserEmail: {
        type: "string",
        title: "Jira User Email",
        description: "Email address for Jira basic-auth (used with the API token).",
        default: "",
      },
      syncIntervalMinutes: {
        type: "number",
        title: "Sync Interval (minutes)",
        description: "How often the background sync job runs.",
        default: 5,
      },
      projectMappings: {
        type: "string",
        title: "Project Mappings (JSON)",
        description: "JSON mapping of Paperclip project IDs to Jira project keys.",
        default: "{}",
      },
    },
  },
  jobs: [
    {
      jobKey: JOB_KEYS.sync,
      displayName: "Jira Sync",
      description: "Periodically polls Jira for changes and syncs them into Paperclip.",
      schedule: "*/5 * * * *",
    },
  ],
  webhooks: [
    {
      endpointKey: WEBHOOK_KEYS.inbound,
      displayName: "Jira Webhook",
      description: "Receives issue and comment events from Jira webhooks.",
    },
  ],
  tools: [
    // ── Read-only (LOW risk) ──────────────────────────────────────────────
    { name: TOOL_NAMES.getJiraIssue, displayName: "Get Jira Issue", description: "Fetch details of a Jira issue by key.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.downloadJiraAttachment, displayName: "Download Jira Attachment", description: "Download an attachment from a Jira issue.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.searchJira, displayName: "Search Jira", description: "Search Jira issues using JQL.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getJiraPullRequests, displayName: "Get Jira Pull Requests", description: "Get pull requests associated with a Jira issue.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getJiraFields, displayName: "Get Jira Fields", description: "Discover available fields for a Jira project or issue type.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getJiraTransitions, displayName: "Get Jira Transitions", description: "Get the available workflow transitions for a Jira issue.", parametersSchema: { type: "object" } },
    // ── Medium risk ───────────────────────────────────────────────────────
    { name: TOOL_NAMES.createJiraTicket, displayName: "Create Jira Ticket", description: "Create a new Jira ticket.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.addJiraComment, displayName: "Add Jira Comment", description: "Add a comment to an existing Jira ticket.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.transitionJiraIssue, displayName: "Transition Jira Issue", description: "Transition a Jira issue to a new status.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.linkJiraIssues, displayName: "Link Jira Issues", description: "Create a link between two Jira issues.", parametersSchema: { type: "object" } },
    // ── High risk ─────────────────────────────────────────────────────────
    { name: TOOL_NAMES.updateJiraTicket, displayName: "Update Jira Ticket", description: "Update an existing Jira ticket with new field values.", parametersSchema: { type: "object" } },
  ],
  ui: {
    slots: [
      {
        type: "page",
        id: SLOT_IDS.page,
        displayName: "Jira",
        exportName: EXPORT_NAMES.page,
        routePath: PAGE_ROUTE,
      },
      {
        type: "settingsPage",
        id: SLOT_IDS.settingsPage,
        displayName: "Jira Settings",
        exportName: EXPORT_NAMES.settingsPage,
      },
      {
        type: "dashboardWidget",
        id: SLOT_IDS.dashboardWidget,
        displayName: "Jira Sync Status",
        exportName: EXPORT_NAMES.dashboardWidget,
      },
      {
        type: "sidebar",
        id: SLOT_IDS.sidebar,
        displayName: "Jira",
        exportName: EXPORT_NAMES.sidebar,
      },
      {
        type: "detailTab",
        id: SLOT_IDS.issueTab,
        displayName: "Jira",
        exportName: EXPORT_NAMES.issueTab,
        entityTypes: ["issue"],
      },
      {
        type: "detailTab",
        id: SLOT_IDS.projectTab,
        displayName: "Jira",
        exportName: EXPORT_NAMES.projectTab,
        entityTypes: ["project"],
      },
    ],
  },
};

export default manifest;
