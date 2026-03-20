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
  displayName: "Confluence",
  description:
    "Link Confluence knowledge base pages to Paperclip issues and projects. " +
    "Give agents access to documentation context during runs and surface " +
    "relevant pages alongside work items.",
  author: "Paperclip",
  categories: ["connector"],
  capabilities: [
    // Data read
    "companies.read",
    "projects.read",
    "issues.read",
    "issue.comments.read",

    // Data write
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
      confluenceBaseUrl: {
        type: "string",
        title: "Confluence Base URL",
        description: "Base URL of your Confluence instance (e.g. https://yourteam.atlassian.net/wiki).",
        default: "",
      },
      confluenceTokenSecretRef: {
        type: "string",
        title: "Confluence API Token (secret ref)",
        description: "Secret reference for the Confluence API token.",
        default: "",
      },
      confluenceUserEmail: {
        type: "string",
        title: "Confluence User Email",
        description: "Email address for Confluence basic-auth (used with the API token).",
        default: "",
      },
      spaceKeys: {
        type: "string",
        title: "Space Keys (comma-separated)",
        description: "Confluence space keys to index and make available to agents.",
        default: "",
      },
      syncIntervalMinutes: {
        type: "number",
        title: "Sync Interval (minutes)",
        description: "How often the background job polls for updated pages.",
        default: 15,
      },
    },
  },
  jobs: [
    {
      jobKey: JOB_KEYS.sync,
      displayName: "Confluence Sync",
      description: "Periodically indexes Confluence pages for agent retrieval and link updates.",
      schedule: "*/15 * * * *",
    },
  ],
  webhooks: [
    {
      endpointKey: WEBHOOK_KEYS.inbound,
      displayName: "Confluence Webhook",
      description: "Receives page_created, page_updated, and comment events from Confluence.",
    },
  ],
  tools: [
    // ── Read-only (LOW risk) ──────────────────────────────────────────────
    { name: TOOL_NAMES.getConfluencePageById, displayName: "Get Confluence Page by ID", description: "Fetch a Confluence page by its unique ID and convert to markdown.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getConfluencePageByTitle, displayName: "Get Confluence Page by Title", description: "Fetch a Confluence page by its title and space key.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getConfluencePageByIdHtml, displayName: "Get Confluence Page HTML by ID", description: "Fetch the raw HTML storage format of a Confluence page by ID.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getConfluencePageByTitleHtml, displayName: "Get Confluence Page HTML by Title", description: "Fetch the raw HTML storage format of a Confluence page by title.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.searchConfluenceWithCql, displayName: "Search Confluence (CQL)", description: "Search Confluence content using CQL (Confluence Query Language).", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.searchConfluencePagesFreetext, displayName: "Search Confluence (Freetext)", description: "Search Confluence pages using free-text query.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getConfluenceSpaces, displayName: "Get Confluence Spaces", description: "List all accessible Confluence spaces.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getConfluencePageTree, displayName: "Get Confluence Page Tree", description: "Get the hierarchical page tree for a space or under a specific page.", parametersSchema: { type: "object" } },
    // ── Medium risk ───────────────────────────────────────────────────────
    { name: TOOL_NAMES.createConfluencePage, displayName: "Create Confluence Page", description: "Create a new Confluence page in a specified space.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.addConfluenceComment, displayName: "Add Confluence Comment", description: "Add a comment to an existing Confluence page.", parametersSchema: { type: "object" } },
    // ── High risk ─────────────────────────────────────────────────────────
    { name: TOOL_NAMES.updateConfluencePage, displayName: "Update Confluence Page", description: "Update an existing Confluence page with new content.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.relocateConfluencePage, displayName: "Relocate Confluence Page", description: "Move or copy a Confluence page to a different parent.", parametersSchema: { type: "object" } },
  ],
  ui: {
    slots: [
      {
        type: "page",
        id: SLOT_IDS.page,
        displayName: "Confluence",
        exportName: EXPORT_NAMES.page,
        routePath: PAGE_ROUTE,
      },
      {
        type: "settingsPage",
        id: SLOT_IDS.settingsPage,
        displayName: "Confluence Settings",
        exportName: EXPORT_NAMES.settingsPage,
      },
      {
        type: "dashboardWidget",
        id: SLOT_IDS.dashboardWidget,
        displayName: "Confluence",
        exportName: EXPORT_NAMES.dashboardWidget,
      },
      {
        type: "sidebar",
        id: SLOT_IDS.sidebar,
        displayName: "Confluence",
        exportName: EXPORT_NAMES.sidebar,
      },
      {
        type: "detailTab",
        id: SLOT_IDS.issueTab,
        displayName: "Confluence",
        exportName: EXPORT_NAMES.issueTab,
        entityTypes: ["issue"],
      },
      {
        type: "detailTab",
        id: SLOT_IDS.projectTab,
        displayName: "Confluence",
        exportName: EXPORT_NAMES.projectTab,
        entityTypes: ["project"],
      },
    ],
  },
};

export default manifest;
