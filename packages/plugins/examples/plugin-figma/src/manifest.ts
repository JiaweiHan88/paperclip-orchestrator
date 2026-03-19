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
  displayName: "Figma",
  description:
    "Link Figma designs to Paperclip issues and projects. Surface design " +
    "previews, track file version history, and give agents access to design " +
    "context during runs.",
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
      figmaTokenSecretRef: {
        type: "string",
        title: "Figma Access Token (secret ref)",
        description: "Secret reference for a Figma personal access token or OAuth token.",
        default: "",
      },
      figmaTeamId: {
        type: "string",
        title: "Figma Team ID",
        description: "The Figma team whose files should be tracked.",
        default: "",
      },
      webhookSecret: {
        type: "string",
        title: "Webhook Passcode (secret ref)",
        description: "Secret reference for Figma webhook passcode verification.",
        default: "",
      },
      syncIntervalMinutes: {
        type: "number",
        title: "Sync Interval (minutes)",
        description: "How often the background job polls for Figma file updates.",
        default: 15,
      },
    },
  },
  jobs: [
    {
      jobKey: JOB_KEYS.sync,
      displayName: "Figma Sync",
      description: "Periodically polls Figma for file version changes and updates linked issues.",
      schedule: "*/15 * * * *",
    },
  ],
  webhooks: [
    {
      endpointKey: WEBHOOK_KEYS.inbound,
      displayName: "Figma Webhook",
      description: "Receives file_update and comment events from Figma webhooks.",
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
        displayName: "Figma",
        exportName: EXPORT_NAMES.page,
        routePath: PAGE_ROUTE,
      },
      {
        type: "settingsPage",
        id: SLOT_IDS.settingsPage,
        displayName: "Figma Settings",
        exportName: EXPORT_NAMES.settingsPage,
      },
      {
        type: "dashboardWidget",
        id: SLOT_IDS.dashboardWidget,
        displayName: "Figma Designs",
        exportName: EXPORT_NAMES.dashboardWidget,
      },
      {
        type: "sidebar",
        id: SLOT_IDS.sidebar,
        displayName: "Figma",
        exportName: EXPORT_NAMES.sidebar,
      },
      {
        type: "detailTab",
        id: SLOT_IDS.issueTab,
        displayName: "Figma",
        exportName: EXPORT_NAMES.issueTab,
        entityTypes: ["issue"],
      },
      {
        type: "detailTab",
        id: SLOT_IDS.projectTab,
        displayName: "Figma",
        exportName: EXPORT_NAMES.projectTab,
        entityTypes: ["project"],
      },
    ],
  },
};

export default manifest;
