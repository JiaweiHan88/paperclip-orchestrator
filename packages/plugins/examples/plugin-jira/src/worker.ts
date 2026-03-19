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

type JiraConfig = {
  jiraBaseUrl?: string;
  jiraTokenSecretRef?: string;
  jiraUserEmail?: string;
  syncIntervalMinutes?: number;
  projectMappings?: string;
};

let currentContext: PluginContext | null = null;

async function getConfig(ctx: PluginContext): Promise<JiraConfig> {
  const raw = await ctx.config.get();
  return raw as JiraConfig;
}

// ---------------------------------------------------------------------------
// Plugin definition
// ---------------------------------------------------------------------------

const plugin: PaperclipPlugin = definePlugin({
  async setup(ctx) {
    currentContext = ctx;
    ctx.logger.info("jira plugin setup starting");

    // ----- Events --------------------------------------------------------
    ctx.events.on("issue.updated", async (event) => {
      ctx.logger.debug("issue.updated event received", { event });
      // TODO: push status/comment changes to Jira
    });

    ctx.events.on("issue.comment.created", async (event) => {
      ctx.logger.debug("issue.comment.created event received", { event });
      // TODO: sync new comments to linked Jira issues
    });

    // ----- Jobs ----------------------------------------------------------
    ctx.jobs.register(JOB_KEYS.sync, async (job: PluginJobContext) => {
      ctx.logger.info("jira sync job running");
      const config = await getConfig(ctx);

      if (!config.jiraBaseUrl || !config.jiraTokenSecretRef) {
        ctx.logger.warn("jira sync skipped — base URL or token not configured");
        return;
      }

      // TODO: resolve secret, poll Jira for recently updated issues,
      //       diff against plugin state cursors, create/update Paperclip issues
    });

    // ----- Data handlers (UI bridge) -------------------------------------
    ctx.data.register("sync-status", async () => {
      const lastSync = await ctx.state.get({ scopeKind: "instance", stateKey: "last-sync-at" });
      const errorCount = await ctx.state.get({ scopeKind: "instance", stateKey: "sync-error-count" });
      return {
        lastSyncAt: lastSync ?? null,
        errorCount: errorCount ?? 0,
        configured: !!(await getConfig(ctx)).jiraBaseUrl,
      };
    });

    ctx.data.register("linked-issue", async (params) => {
      const issueId = params.issueId as string | undefined;
      if (!issueId) return null;
      const linked = await ctx.state.get({ scopeKind: "instance", stateKey: `issue-link:${issueId}` });
      return linked ?? null;
    });

    // ----- Actions (UI bridge) -------------------------------------------
    ctx.actions.register("trigger-sync", async () => {
      ctx.logger.info("manual sync triggered from UI");
      // TODO: run sync logic on demand
      return { ok: true };
    });

    // ----- Tools (declared later) ----------------------------------------
    // Tools will be registered in a future pass via ctx.tools.register().

    ctx.logger.info("jira plugin setup complete");
  },

  async onWebhook(input: PluginWebhookInput) {
    const ctx = currentContext;
    if (!ctx) return;

    ctx.logger.info("jira inbound webhook received", {
      endpointKey: input.endpointKey,
      requestId: input.requestId,
    });

    if (input.endpointKey !== WEBHOOK_KEYS.inbound) return;

    // TODO: parse Jira webhook payload, handle issue_created,
    //       issue_updated, comment_created events idempotently
  },

  async onHealth(): Promise<PluginHealthDiagnostics> {
    const ctx = currentContext;
    if (!ctx) return { status: "degraded", message: "Jira plugin not yet initialized" };
    const config = await getConfig(ctx);
    const configured = !!config.jiraBaseUrl && !!config.jiraTokenSecretRef;
    return {
      status: configured ? "ok" : "degraded",
      message: configured
        ? "Jira plugin configured and ready"
        : "Jira plugin loaded but not configured — set Base URL and API token in settings",
    };
  },
});

export default plugin;
runWorker(plugin, import.meta.url);
