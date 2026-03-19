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

type GerritConfig = {
  gerritBaseUrl?: string;
  gerritTokenSecretRef?: string;
  gerritUsername?: string;
  syncIntervalMinutes?: number;
  projectMappings?: string;
};

let currentContext: PluginContext | null = null;

async function getConfig(ctx: PluginContext): Promise<GerritConfig> {
  const raw = await ctx.config.get();
  return raw as GerritConfig;
}

// ---------------------------------------------------------------------------
// Plugin definition
// ---------------------------------------------------------------------------

const plugin: PaperclipPlugin = definePlugin({
  async setup(ctx) {
    currentContext = ctx;
    ctx.logger.info("gerrit plugin setup starting");

    // ----- Events --------------------------------------------------------
    ctx.events.on("issue.updated", async (event) => {
      ctx.logger.debug("issue.updated event received", { event });
      // TODO: if issue is linked to a Gerrit change, post a comment on the change
    });

    // ----- Jobs ----------------------------------------------------------
    ctx.jobs.register(JOB_KEYS.sync, async (job: PluginJobContext) => {
      ctx.logger.info("gerrit sync job running");
      const config = await getConfig(ctx);

      if (!config.gerritBaseUrl || !config.gerritTokenSecretRef) {
        ctx.logger.warn("gerrit sync skipped — base URL or credentials not configured");
        return;
      }

      // TODO: resolve secret, query Gerrit REST API for recently updated changes,
      //       match to linked Paperclip issues, update review status in plugin state
    });

    // ----- Data handlers (UI bridge) -------------------------------------
    ctx.data.register("sync-status", async () => {
      const lastSync = await ctx.state.get({ scopeKind: "instance", stateKey: "last-sync-at" });
      const errorCount = await ctx.state.get({ scopeKind: "instance", stateKey: "sync-error-count" });
      return {
        lastSyncAt: lastSync ?? null,
        errorCount: errorCount ?? 0,
        configured: !!(await getConfig(ctx)).gerritBaseUrl,
      };
    });

    ctx.data.register("linked-change", async (params) => {
      const issueId = params.issueId as string | undefined;
      if (!issueId) return null;
      const linked = await ctx.state.get({ scopeKind: "instance", stateKey: `change-link:${issueId}` });
      return linked ?? null;
    });

    // ----- Actions (UI bridge) -------------------------------------------
    ctx.actions.register("trigger-sync", async () => {
      ctx.logger.info("manual gerrit sync triggered from UI");
      // TODO: run sync logic on demand
      return { ok: true };
    });

    // ----- Tools (declared later) ----------------------------------------
    // Tools will be registered in a future pass via ctx.tools.register().

    ctx.logger.info("gerrit plugin setup complete");
  },

  async onWebhook(input: PluginWebhookInput) {
    const ctx = currentContext;
    if (!ctx) return;

    ctx.logger.info("gerrit stream-event webhook received", {
      endpointKey: input.endpointKey,
      requestId: input.requestId,
    });

    if (input.endpointKey !== WEBHOOK_KEYS.streamEvents) return;

    // TODO: parse Gerrit event (patchset-created, comment-added,
    //       change-merged, etc.), update linked Paperclip issues
  },

  async onHealth(): Promise<PluginHealthDiagnostics> {
    const ctx = currentContext;
    if (!ctx) return { status: "degraded", message: "Gerrit plugin not yet initialized" };
    const config = await getConfig(ctx);
    const configured = !!config.gerritBaseUrl && !!config.gerritTokenSecretRef;
    return {
      status: configured ? "ok" : "degraded",
      message: configured
        ? "Gerrit plugin configured and ready"
        : "Gerrit plugin loaded but not configured — set Base URL and credentials in settings",
    };
  },
});

export default plugin;
runWorker(plugin, import.meta.url);
