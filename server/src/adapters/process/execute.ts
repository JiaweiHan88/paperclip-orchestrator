import type { AdapterExecutionContext, AdapterExecutionResult } from "../types.js";
import {
  asString,
  asNumber,
  asStringArray,
  parseObject,
  buildPaperclipEnv,
  redactEnvForLogs,
  runChildProcess,
} from "../utils.js";

/** Read a non-empty trimmed string or return null. */
function readNonEmpty(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

export async function execute(ctx: AdapterExecutionContext): Promise<AdapterExecutionResult> {
  const { runId, agent, config, context, onLog, onMeta, authToken } = ctx;
  const command = asString(config.command, "");
  if (!command) throw new Error("Process adapter missing command");

  const args = asStringArray(config.args);
  const cwd = asString(config.cwd, process.cwd());
  const envConfig = parseObject(config.env);
  const env: Record<string, string> = { ...buildPaperclipEnv(agent) };

  // Inject the heartbeat run ID for audit trail correlation.
  if (runId) {
    env.PAPERCLIP_RUN_ID = runId;
  }

  // ---------------------------------------------------------------------------
  // Wake context env vars — match the canonical pattern from claude adapter.
  // Use fallback keys because different wakeup callers populate different names.
  // ---------------------------------------------------------------------------
  const wakeTaskId =
    readNonEmpty(context?.taskId) ??
    readNonEmpty(context?.issueId) ??
    null;
  const wakeReason = readNonEmpty(context?.wakeReason);
  const wakeCommentId =
    readNonEmpty(context?.wakeCommentId) ??
    readNonEmpty(context?.commentId) ??
    null;
  const approvalId = readNonEmpty(context?.approvalId);
  const approvalStatus = readNonEmpty(context?.approvalStatus);
  const linkedIssueIds = Array.isArray(context?.issueIds)
    ? context.issueIds.filter((v: unknown): v is string => typeof v === "string" && (v as string).trim().length > 0)
    : [];

  if (wakeTaskId) env.PAPERCLIP_TASK_ID = wakeTaskId;
  if (wakeReason) env.PAPERCLIP_WAKE_REASON = wakeReason;
  if (wakeCommentId) env.PAPERCLIP_WAKE_COMMENT_ID = wakeCommentId;
  if (approvalId) env.PAPERCLIP_APPROVAL_ID = approvalId;
  if (approvalStatus) env.PAPERCLIP_APPROVAL_STATUS = approvalStatus;
  if (linkedIssueIds.length > 0) env.PAPERCLIP_LINKED_ISSUE_IDS = linkedIssueIds.join(",");

  // ---------------------------------------------------------------------------
  // Workspace context — let child process know where its workspace is.
  // ---------------------------------------------------------------------------
  const workspaceContext = parseObject(context?.paperclipWorkspace);
  const workspaceCwd = asString(workspaceContext.cwd, "");
  const workspaceSource = asString(workspaceContext.source, "");
  const workspaceStrategy = asString(workspaceContext.strategy, "");
  const workspaceId = asString(workspaceContext.workspaceId, "") || null;
  const workspaceRepoUrl = asString(workspaceContext.repoUrl, "") || null;
  const workspaceRepoRef = asString(workspaceContext.repoRef, "") || null;
  const workspaceBranch = asString(workspaceContext.branchName, "") || null;
  const workspaceWorktreePath = asString(workspaceContext.worktreePath, "") || null;
  const agentHome = asString(workspaceContext.agentHome, "") || null;
  const workspaceHints = Array.isArray(context?.paperclipWorkspaces)
    ? context.paperclipWorkspaces.filter(
        (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null,
      )
    : [];

  if (workspaceCwd) env.PAPERCLIP_WORKSPACE_CWD = workspaceCwd;
  if (workspaceSource) env.PAPERCLIP_WORKSPACE_SOURCE = workspaceSource;
  if (workspaceStrategy) env.PAPERCLIP_WORKSPACE_STRATEGY = workspaceStrategy;
  if (workspaceId) env.PAPERCLIP_WORKSPACE_ID = workspaceId;
  if (workspaceRepoUrl) env.PAPERCLIP_WORKSPACE_REPO_URL = workspaceRepoUrl;
  if (workspaceRepoRef) env.PAPERCLIP_WORKSPACE_REPO_REF = workspaceRepoRef;
  if (workspaceBranch) env.PAPERCLIP_WORKSPACE_BRANCH = workspaceBranch;
  if (workspaceWorktreePath) env.PAPERCLIP_WORKSPACE_WORKTREE_PATH = workspaceWorktreePath;
  if (agentHome) env.AGENT_HOME = agentHome;
  if (workspaceHints.length > 0) env.PAPERCLIP_WORKSPACES_JSON = JSON.stringify(workspaceHints);

  // ---------------------------------------------------------------------------
  // Runtime services — MCP servers and other runtime-provisioned services.
  // ---------------------------------------------------------------------------
  const runtimeServiceIntents = Array.isArray(context?.paperclipRuntimeServiceIntents)
    ? context.paperclipRuntimeServiceIntents.filter(
        (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null,
      )
    : [];
  const runtimeServices = Array.isArray(context?.paperclipRuntimeServices)
    ? context.paperclipRuntimeServices.filter(
        (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null,
      )
    : [];
  const runtimePrimaryUrl = asString(context?.paperclipRuntimePrimaryUrl, "");

  if (runtimeServiceIntents.length > 0) env.PAPERCLIP_RUNTIME_SERVICE_INTENTS_JSON = JSON.stringify(runtimeServiceIntents);
  if (runtimeServices.length > 0) env.PAPERCLIP_RUNTIME_SERVICES_JSON = JSON.stringify(runtimeServices);
  if (runtimePrimaryUrl) env.PAPERCLIP_RUNTIME_PRIMARY_URL = runtimePrimaryUrl;

  // ---------------------------------------------------------------------------
  // User-provided env overrides from config.env — applied after all system vars
  // so operator values take precedence.
  // ---------------------------------------------------------------------------
  const hasExplicitApiKey =
    typeof envConfig.PAPERCLIP_API_KEY === "string" && (envConfig.PAPERCLIP_API_KEY as string).trim().length > 0;
  for (const [k, v] of Object.entries(envConfig)) {
    if (typeof v === "string") env[k] = v;
  }

  // Inject agent JWT only when the user hasn't explicitly set their own key.
  if (!hasExplicitApiKey && authToken) {
    env.PAPERCLIP_API_KEY = authToken;
  }

  const timeoutSec = asNumber(config.timeoutSec, 0);
  const graceSec = asNumber(config.graceSec, 15);

  if (onMeta) {
    await onMeta({
      adapterType: "process",
      command,
      cwd,
      commandArgs: args,
      env: redactEnvForLogs(env),
    });
  }

  const proc = await runChildProcess(runId, command, args, {
    cwd,
    env,
    timeoutSec,
    graceSec,
    onLog,
  });

  if (proc.timedOut) {
    return {
      exitCode: proc.exitCode,
      signal: proc.signal,
      timedOut: true,
      errorMessage: `Timed out after ${timeoutSec}s`,
    };
  }

  if ((proc.exitCode ?? 0) !== 0) {
    return {
      exitCode: proc.exitCode,
      signal: proc.signal,
      timedOut: false,
      errorMessage: `Process exited with code ${proc.exitCode ?? -1}`,
      resultJson: {
        stdout: proc.stdout,
        stderr: proc.stderr,
      },
    };
  }

  return {
    exitCode: proc.exitCode,
    signal: proc.signal,
    timedOut: false,
    resultJson: {
      stdout: proc.stdout,
      stderr: proc.stderr,
    },
  };
}
