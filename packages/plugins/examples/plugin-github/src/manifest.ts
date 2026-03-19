import type { PaperclipPluginManifestV1 } from "@paperclipai/plugin-sdk";
import {
  EXPORT_NAMES,
  JOB_KEYS,
  PAGE_ROUTE,
  PLUGIN_ID,
  PLUGIN_VERSION,
  SLOT_IDS,
  WEBHOOK_KEYS,
} from "./constants.js";

const manifest: PaperclipPluginManifestV1 = {
  id: PLUGIN_ID,
  apiVersion: 1,
  version: PLUGIN_VERSION,
  displayName: "GitHub",
  description:
    "Sync issues, pull requests, and comments between Paperclip and GitHub. " +
    "Provides webhook-driven and polling-based sync, plus agent tools for " +
    "querying GitHub during runs.",
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
    "events.emit",
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
      githubTokenSecretRef: {
        type: "string",
        title: "GitHub Token (secret ref)",
        description: "Secret reference for a GitHub PAT or GitHub App installation token.",
        default: "",
      },
      githubApiBaseUrl: {
        type: "string",
        title: "GitHub API Base URL",
        description: "API base URL. Use https://api.github.com for github.com, or your GHES URL.",
        default: "https://api.github.com",
      },
      repoMappings: {
        type: "string",
        title: "Repo Mappings (JSON)",
        description: "JSON mapping of Paperclip project IDs to GitHub owner/repo pairs.",
        default: "{}",
      },
      syncIntervalMinutes: {
        type: "number",
        title: "Sync Interval (minutes)",
        description: "How often the background sync job runs.",
        default: 5,
      },
      webhookSecret: {
        type: "string",
        title: "Webhook Secret (secret ref)",
        description: "Secret reference for GitHub webhook signature verification.",
        default: "",
      },
    },
  },
  jobs: [
    {
      jobKey: JOB_KEYS.sync,
      displayName: "GitHub Sync",
      description: "Periodically polls GitHub for changes and syncs them into Paperclip.",
      schedule: "*/5 * * * *",
    },
  ],
  webhooks: [
    {
      endpointKey: WEBHOOK_KEYS.inbound,
      displayName: "GitHub Webhook",
      description: "Receives issue, PR, and comment events from GitHub webhooks.",
    },
  ],
  tools: [
    // Tools will be declared in a future pass.
  ],
  ui: {
    slots: [
      {
        type: "page",
        id: SLOT_IDS.page,
        displayName: "GitHub",
        exportName: EXPORT_NAMES.page,
        routePath: PAGE_ROUTE,
      },
      {
        type: "settingsPage",
        id: SLOT_IDS.settingsPage,
        displayName: "GitHub Settings",
        exportName: EXPORT_NAMES.settingsPage,
      },
      {
        type: "dashboardWidget",
        id: SLOT_IDS.dashboardWidget,
        displayName: "GitHub Sync Status",
        exportName: EXPORT_NAMES.dashboardWidget,
      },
      {
        type: "sidebar",
        id: SLOT_IDS.sidebar,
        displayName: "GitHub",
        exportName: EXPORT_NAMES.sidebar,
      },
      {
        type: "detailTab",
        id: SLOT_IDS.issueTab,
        displayName: "GitHub",
        exportName: EXPORT_NAMES.issueTab,
        entityTypes: ["issue"],
      },
      {
        type: "detailTab",
        id: SLOT_IDS.projectTab,
        displayName: "GitHub",
        exportName: EXPORT_NAMES.projectTab,
        entityTypes: ["project"],
      },
    ],
  },
};

export default manifest;
