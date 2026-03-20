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
    // ── Read-only (LOW risk) ──────────────────────────────────────────────
    { name: TOOL_NAMES.getPullRequestDiff, displayName: "Get Pull Request Diff", description: "Get the diff for a pull request.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getCommitDiff, displayName: "Get Commit Diff", description: "Get the diff for a commit.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.batchAnalyzePullRequest, displayName: "Batch Analyze Pull Requests", description: "Analyze multiple pull requests for relationships and patterns.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getPullRequestsBetweenCommits, displayName: "Get PRs Between Commits", description: "List pull requests between two commits.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getPullRequest, displayName: "Get Pull Request", description: "Get pull request details.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.searchPullRequests, displayName: "Search Pull Requests", description: "Search pull requests in a repository.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getIssueTimeLine, displayName: "Get Issue Timeline", description: "Get the event timeline for a GitHub issue.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getIssuesFromProjectBoard, displayName: "Get Issues From Project Board", description: "List filtered issues from a GitHub project board.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getProjectFields, displayName: "Get Project Fields", description: "Get field definitions for a GitHub project.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getRepoHistory, displayName: "Get Repo History", description: "Get commit history for a repository.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getRepoStats, displayName: "Get Repo Stats", description: "Get statistics for a repository.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getRepoTree, displayName: "Get Repo Tree", description: "Get the file tree for a repository.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getFileContent, displayName: "Get File Content", description: "Read a file from a repository at a given ref.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getZuulBuildsetsForPr, displayName: "Get Zuul Buildsets for PR", description: "Get Zuul CI buildsets associated with a pull request.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getPullRequestStructured, displayName: "Get Pull Request (Structured)", description: "Get structured pull request data.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getPullRequestState, displayName: "Get Pull Request State", description: "Get the current status and merge state of a pull request.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.getRepoFolderFilesPath, displayName: "Get Repo Folder Files", description: "List files in a repository folder.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.searchCode, displayName: "Search Code", description: "Search code across repositories.", parametersSchema: { type: "object" } },
    // ── Medium risk ───────────────────────────────────────────────────────
    { name: TOOL_NAMES.addCommentToPullRequest, displayName: "Add Comment to Pull Request", description: "Post a comment on a pull request.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.addLabelToPullRequest, displayName: "Add Label to Pull Request", description: "Add a label to a pull request.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.removeLabelFromPullRequest, displayName: "Remove Label from Pull Request", description: "Remove a label from a pull request.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.createReactionToPullRequestComment, displayName: "Create Reaction to PR Comment", description: "Add an emoji reaction to a pull request comment.", parametersSchema: { type: "object" } },
    // ── High risk ─────────────────────────────────────────────────────────
    { name: TOOL_NAMES.updatePullRequestDescription, displayName: "Update Pull Request Description", description: "Replace the description of a pull request.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.injectToPullRequestDescription, displayName: "Inject to Pull Request Description", description: "Append a section to an existing pull request description.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.createBranch, displayName: "Create Branch", description: "Create a new branch in a repository.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.createCommitOnBranch, displayName: "Create Commit on Branch", description: "Commit files to an existing branch.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.createPullRequest, displayName: "Create Pull Request", description: "Open a new pull request.", parametersSchema: { type: "object" } },
    { name: TOOL_NAMES.createIssue, displayName: "Create Issue", description: "Create a new GitHub issue.", parametersSchema: { type: "object" } },
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
