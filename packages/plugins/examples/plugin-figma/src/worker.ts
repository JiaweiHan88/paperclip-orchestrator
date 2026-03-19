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

type FigmaConfig = {
  figmaTokenSecretRef?: string;
  figmaTeamId?: string;
  webhookSecret?: string;
  syncIntervalMinutes?: number;
};

let currentContext: PluginContext | null = null;

async function getConfig(ctx: PluginContext): Promise<FigmaConfig> {
  const raw = await ctx.config.get();
  return raw as FigmaConfig;
}

// ---------------------------------------------------------------------------
// Plugin definition
// ---------------------------------------------------------------------------

const plugin: PaperclipPlugin = definePlugin({
  async setup(ctx) {
    currentContext = ctx;
    ctx.logger.info("figma plugin setup starting");

    // ----- Events --------------------------------------------------------
    ctx.events.on("issue.created", async (event) => {
      ctx.logger.debug("issue.created event received", { event });
      // TODO: auto-link Figma designs when issue contains Figma URLs
    });

    // ----- Jobs ----------------------------------------------------------
    ctx.jobs.register(JOB_KEYS.sync, async (job: PluginJobContext) => {
      ctx.logger.info("figma sync job running");
      const config = await getConfig(ctx);

      if (!config.figmaTokenSecretRef) {
        ctx.logger.warn("figma sync skipped — token not configured");
        return;
      }

      // TODO: resolve secret, poll Figma REST API for file version changes,
      //       update linked issue state, cache thumbnail URLs
    });

    // ----- Data handlers (UI bridge) -------------------------------------
    ctx.data.register("sync-status", async () => {
      const lastSync = await ctx.state.get({ scopeKind: "instance", stateKey: "last-sync-at" });
      const errorCount = await ctx.state.get({ scopeKind: "instance", stateKey: "sync-error-count" });
      return {
        lastSyncAt: lastSync ?? null,
        errorCount: errorCount ?? 0,
        configured: !!(await getConfig(ctx)).figmaTokenSecretRef,
      };
    });

    ctx.data.register("linked-designs", async (params) => {
      const issueId = params.issueId as string | undefined;
      if (!issueId) return [];
      const designs = await ctx.state.get({ scopeKind: "instance", stateKey: `design-links:${issueId}` });
      return designs ?? [];
    });

    // ----- Actions (UI bridge) -------------------------------------------
    ctx.actions.register("trigger-sync", async () => {
      ctx.logger.info("manual figma sync triggered from UI");
      // TODO: run sync logic on demand
      return { ok: true };
    });

    // ----- Tools (declared later) ----------------------------------------
    // Tools will be registered in a future pass via ctx.tools.register().

    ctx.logger.info("figma plugin setup complete");
  },

  async onWebhook(input: PluginWebhookInput) {
    const ctx = currentContext;
    if (!ctx) return;

    ctx.logger.info("figma inbound webhook received", {
      endpointKey: input.endpointKey,
      requestId: input.requestId,
    });

    if (input.endpointKey !== WEBHOOK_KEYS.inbound) return;

    // TODO: verify passcode, parse Figma webhook payload,
    //       handle FILE_UPDATE, FILE_COMMENT events
  },

  async onHealth(): Promise<PluginHealthDiagnostics> {
    const ctx = currentContext;
    if (!ctx) return { status: "degraded", message: "Figma plugin not yet initialized" };
    const config = await getConfig(ctx);
    const configured = !!config.figmaTokenSecretRef;
    return {
      status: configured ? "ok" : "degraded",
      message: configured
        ? "Figma plugin configured and ready"
        : "Figma plugin loaded but not configured — set access token in settings",
    };
  },
});

export default plugin;
runWorker(plugin, import.meta.url);
