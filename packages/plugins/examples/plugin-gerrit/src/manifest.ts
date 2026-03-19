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
  displayName: "Gerrit",
  description:
    "Track Gerrit code reviews and change status inside Paperclip. " +
    "Links Paperclip issues to Gerrit changes, syncs review scores, and " +
    "provides agent tools for querying Gerrit during runs.",
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
      gerritBaseUrl: {
        type: "string",
        title: "Gerrit Base URL",
        description: "Base URL of your Gerrit instance (e.g. https://gerrit.example.com).",
        default: "",
      },
      gerritTokenSecretRef: {
        type: "string",
        title: "Gerrit HTTP Credentials (secret ref)",
        description: "Secret reference for Gerrit HTTP password or access token.",
        default: "",
      },
      gerritUsername: {
        type: "string",
        title: "Gerrit Username",
        description: "Username for Gerrit HTTP authentication.",
        default: "",
      },
      syncIntervalMinutes: {
        type: "number",
        title: "Sync Interval (minutes)",
        description: "How often the background sync job polls for updated changes.",
        default: 5,
      },
      projectMappings: {
        type: "string",
        title: "Project Mappings (JSON)",
        description: "JSON mapping of Paperclip project IDs to Gerrit project names.",
        default: "{}",
      },
    },
  },
  jobs: [
    {
      jobKey: JOB_KEYS.sync,
      displayName: "Gerrit Sync",
      description: "Periodically polls Gerrit for updated changes and syncs review status.",
      schedule: "*/5 * * * *",
    },
  ],
  webhooks: [
    {
      endpointKey: WEBHOOK_KEYS.streamEvents,
      displayName: "Gerrit Stream Events",
      description: "Receives change and review events forwarded from Gerrit stream-events.",
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
        displayName: "Gerrit",
        exportName: EXPORT_NAMES.page,
        routePath: PAGE_ROUTE,
      },
      {
        type: "settingsPage",
        id: SLOT_IDS.settingsPage,
        displayName: "Gerrit Settings",
        exportName: EXPORT_NAMES.settingsPage,
      },
      {
        type: "dashboardWidget",
        id: SLOT_IDS.dashboardWidget,
        displayName: "Gerrit Reviews",
        exportName: EXPORT_NAMES.dashboardWidget,
      },
      {
        type: "sidebar",
        id: SLOT_IDS.sidebar,
        displayName: "Gerrit",
        exportName: EXPORT_NAMES.sidebar,
      },
      {
        type: "detailTab",
        id: SLOT_IDS.issueTab,
        displayName: "Gerrit",
        exportName: EXPORT_NAMES.issueTab,
        entityTypes: ["issue"],
      },
      {
        type: "detailTab",
        id: SLOT_IDS.projectTab,
        displayName: "Gerrit",
        exportName: EXPORT_NAMES.projectTab,
        entityTypes: ["project"],
      },
    ],
  },
};

export default manifest;
