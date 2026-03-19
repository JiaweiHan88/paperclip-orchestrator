import { definePlugin, runWorker } from "@paperclipai/plugin-sdk";
import type {
  PaperclipPlugin,
  PluginContext,
  PluginHealthDiagnostics,
  PluginJobContext,
  PluginWebhookInput,
} from "@paperclipai/plugin-sdk";
import { JOB_KEYS, WEBHOOK_KEYS } from "./constants.js";

// ---------------------------------------------------------------------------
// Config shape
// ---------------------------------------------------------------------------

type GitHubConfig = {
  githubTokenSecretRef?: string;
  githubApiBaseUrl?: string;
  repoMappings?: string;
  syncIntervalMinutes?: number;
  webhookSecret?: string;
};

let currentContext: PluginContext | null = null;

async function getConfig(ctx: PluginContext): Promise<GitHubConfig> {
  const raw = await ctx.config.get();
  return raw as GitHubConfig;
}

// ---------------------------------------------------------------------------
// Plugin definition
// ---------------------------------------------------------------------------

const plugin: PaperclipPlugin = definePlugin({
  async setup(ctx) {
    currentContext = ctx;
    ctx.logger.info("github plugin setup starting");

    // ----- Events --------------------------------------------------------
    ctx.events.on("issue.updated", async (event) => {
      ctx.logger.debug("issue.updated event received", { event });
      // TODO: push status changes to linked GitHub issues
    });

    ctx.events.on("issue.comment.created", async (event) => {
      ctx.logger.debug("issue.comment.created event received", { event });
      // TODO: sync comments to linked GitHub issues
    });

    // ----- Jobs ----------------------------------------------------------
    ctx.jobs.register(JOB_KEYS.sync, async (job: PluginJobContext) => {
      ctx.logger.info("github sync job running");
      const config = await getConfig(ctx);

      if (!config.githubTokenSecretRef) {
        ctx.logger.warn("github sync skipped — token not configured");
        return;
      }

      // TODO: resolve secret, poll GitHub for recently updated issues/PRs,
      //       diff against plugin state cursors, create/update Paperclip issues
    });

    // ----- Data handlers (UI bridge) -------------------------------------
    ctx.data.register("sync-status", async () => {
      const lastSync = await ctx.state.get({ scopeKind: "instance", stateKey: "last-sync-at" });
      const errorCount = await ctx.state.get({ scopeKind: "instance", stateKey: "sync-error-count" });
      return {
        lastSyncAt: lastSync ?? null,
        errorCount: errorCount ?? 0,
        configured: !!(await getConfig(ctx)).githubTokenSecretRef,
      };
    });

    ctx.data.register("linked-issue", async (params) => {
      const issueId = params.issueId as string | undefined;
      if (!issueId) return null;
      const linked = await ctx.state.get({ scopeKind: "instance", stateKey: `issue-link:${issueId}` });
      return linked ?? null;
    });

    ctx.data.register("linked-prs", async (params) => {
      const issueId = params.issueId as string | undefined;
      if (!issueId) return [];
      const prs = await ctx.state.get({ scopeKind: "instance", stateKey: `pr-links:${issueId}` });
      return prs ?? [];
    });

    // ----- Actions (UI bridge) -------------------------------------------
    ctx.actions.register("trigger-sync", async () => {
      ctx.logger.info("manual sync triggered from UI");
      // TODO: run sync logic on demand
      return { ok: true };
    });

    // ----- Tools (declared later) ----------------------------------------
    // Tools will be registered in a future pass via ctx.tools.register().

    ctx.logger.info("github plugin setup complete");
  },

  async onWebhook(input: PluginWebhookInput) {
    const ctx = currentContext;
    if (!ctx) return;

    ctx.logger.info("github inbound webhook received", {
      endpointKey: input.endpointKey,
      requestId: input.requestId,
    });

    if (input.endpointKey !== WEBHOOK_KEYS.inbound) return;

    // TODO: verify signature, parse GitHub event payload,
    //       handle issues, issue_comment, pull_request events idempotently
  },

  async onHealth(): Promise<PluginHealthDiagnostics> {
    const ctx = currentContext;
    if (!ctx) return { status: "degraded", message: "GitHub plugin not yet initialized" };
    const config = await getConfig(ctx);
    const configured = !!config.githubTokenSecretRef;
    return {
      status: configured ? "ok" : "degraded",
      message: configured
        ? "GitHub plugin configured and ready"
        : "GitHub plugin loaded but not configured — set token in settings",
    };
  },
});

export default plugin;
runWorker(plugin, import.meta.url);
