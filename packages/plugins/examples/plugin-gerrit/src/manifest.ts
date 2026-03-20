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
    // ── Read-only (LOW risk) ──────────────────────────────────────────────
    { name: TOOL_NAMES.queryChanges, displayName: "Query Changes", description: "Search Gerrit changes by query string.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.queryChangesByDate, displayName: "Query Changes by Date", description: "Search Gerrit changes filtered by date range.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getMostRecentCl, displayName: "Get Most Recent CL", description: "Get the most recent change (CL) for a query.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getChangeDetails, displayName: "Get Change Details", description: "Get detailed metadata for a Gerrit change.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.changesSubmittedTogether, displayName: "Changes Submitted Together", description: "Get changes that were submitted in the same submission.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.listChangeComments, displayName: "List Change Comments", description: "List all review comments on a Gerrit change.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getCommitMessage, displayName: "Get Commit Message", description: "Get the commit message for a Gerrit change.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getBugsFromCl, displayName: "Get Bugs from CL", description: "Extract bug/issue references from a Gerrit change's commit message.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getFileContent, displayName: "Get File Content", description: "Read a file from a Gerrit change at a specific revision.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.listChangeFiles, displayName: "List Change Files", description: "List files modified in a Gerrit change.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getChangeDiff, displayName: "Get Change Diff", description: "Get the full diff for a Gerrit change.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getFileDiff, displayName: "Get File Diff", description: "Get the diff for a single file in a Gerrit change.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getProjectBranches, displayName: "Get Project Branches", description: "List branches for a Gerrit project.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.suggestReviewers, displayName: "Suggest Reviewers", description: "Suggest reviewers for a Gerrit change.", parametersSchema: { type: "object" } },
    // ── Medium risk ───────────────────────────────────────────────────────
    { name: TOOL_NAMES.addReviewer, displayName: "Add Reviewer", description: "Add a reviewer to a Gerrit change.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.postReviewComment, displayName: "Post Review Comment", description: "Post an inline review comment on a Gerrit change.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.setReadyForReview, displayName: "Set Ready for Review", description: "Mark a Gerrit change as ready for review.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.setWorkInProgress, displayName: "Set Work In Progress", description: "Mark a Gerrit change as work in progress.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.setTopic, displayName: "Set Topic", description: "Set the topic for a Gerrit change.", parametersSchema: { type: "object" } },
    // ── High risk ─────────────────────────────────────────────────────────
    { name: TOOL_NAMES.createChange, displayName: "Create Change", description: "Create a new Gerrit change.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.abandonChange, displayName: "Abandon Change", description: "Abandon a Gerrit change.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.revertChange, displayName: "Revert Change", description: "Revert a submitted Gerrit change.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.revertSubmission, displayName: "Revert Submission", description: "Revert an entire Gerrit submission.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.setReview, displayName: "Set Review", description: "Submit review scores and labels on a Gerrit change.", parametersSchema: { type: "object" } },
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
