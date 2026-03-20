import { definePlugin, runWorker } from "@paperclipai/plugin-sdk";
import type {
  PaperclipPlugin,
  PluginContext,
  PluginHealthDiagnostics,
  PluginJobContext,
  PluginWebhookInput,
} from "@paperclipai/plugin-sdk";
import { createBridgeClient } from "@paperclipai/adapter-utils";
import { JOB_KEYS, WEBHOOK_KEYS } from "./constants.js";

// ---------------------------------------------------------------------------
// Bridge tool registration with retry
// ---------------------------------------------------------------------------

async function resolveBridgeUrl(envUrl: string): Promise<string> {
  if (process.env.AI_TOOLS_BRIDGE_URL) return process.env.AI_TOOLS_BRIDGE_URL;
  const candidates =
    envUrl === "http://ai-tools-bridge:8000"
      ? ["http://localhost:8000", "http://ai-tools-bridge:8000"]
      : [envUrl];
  for (const url of candidates) {
    try {
      const res = await fetch(`${url}/health`, { signal: AbortSignal.timeout(2_000) });
      if (res.ok) return url;
    } catch { /* try next */ }
  }
  return envUrl;
}

async function registerBridgeTools(
  ctx: PluginContext,
  packageSlug: string,
  configuredUrl: string,
  buildCredentials: (config: ReturnType<typeof getConfig> extends Promise<infer T> ? T : never) => Promise<Record<string, unknown>>,
  logPrefix: string,
): Promise<void> {
  const delays = [2_000, 5_000, 10_000, 20_000, 30_000, 60_000, 120_000, 180_000];
  for (let attempt = 0; attempt <= delays.length; attempt++) {
    try {
      const bridgeUrl = await resolveBridgeUrl(configuredUrl);
      const bridge = createBridgeClient(bridgeUrl, packageSlug);
      const tools = await bridge.getToolManifest();
      for (const tool of tools) {
        ctx.tools.register(
          tool.name,
          { displayName: tool.display_name, description: tool.description, parametersSchema: tool.parameters_schema },
          async (params, _runCtx) => {
            const config = await getConfig(ctx);
            const credentials = await buildCredentials(config);
            const execUrl = await resolveBridgeUrl(configuredUrl);
            const execBridge = createBridgeClient(execUrl, packageSlug);
            const result = await execBridge.execute(tool.name, params as Record<string, unknown>, credentials);
            if (result.error) return { error: result.error };
            return { content: result.content, data: result.data };
          },
        );
      }
      ctx.logger.info(`${logPrefix}: registered tools from bridge`, { count: tools.length, bridgeUrl });
      return;
    } catch (err) {
      if (attempt === delays.length) {
        ctx.logger.warn(`${logPrefix}: bridge unavailable after all retries — tools not registered`, { configuredUrl, error: (err as Error).message });
        return;
      }
      ctx.logger.debug(`${logPrefix}: bridge not ready, retrying in ${delays[attempt]! / 1000}s`, { attempt });
      await new Promise((r) => setTimeout(r, delays[attempt]!));
    }
  }
}

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
let currentBridgeUrl: string = "http://ai-tools-bridge:8000";

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

    // ----- Tools --------------------------------------------------------
    const bridgeUrl = process.env.AI_TOOLS_BRIDGE_URL ?? "http://ai-tools-bridge:8000";
    currentBridgeUrl = bridgeUrl;

    void registerBridgeTools(
      ctx,
      "gerrit",
      bridgeUrl,
      async (config) => {
        const credentials: Record<string, unknown> = {};
        if (config.gerritBaseUrl) credentials["gerrit_base_url"] = config.gerritBaseUrl;
        if (config.gerritUsername) credentials["username"] = config.gerritUsername;
        if (config.gerritTokenSecretRef) {
          try {
            credentials["token"] = await ctx.secrets.resolve(config.gerritTokenSecretRef);
          } catch {
            ctx.logger.warn("gerrit: failed to resolve token secret", { ref: config.gerritTokenSecretRef });
          }
        }
        return credentials;
      },
      "gerrit plugin",
    );

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

    const resolvedUrl = await resolveBridgeUrl(currentBridgeUrl);
    const bridge = createBridgeClient(resolvedUrl, "gerrit");
    const bridgeOk = await bridge.isHealthy();

    if (!configured) {
      return { status: "degraded", message: "Gerrit plugin loaded but not configured — set Base URL and credentials in settings" };
    }
    if (!bridgeOk) {
      return { status: "degraded", message: `Gerrit plugin configured but AI tools bridge is unreachable at ${currentBridgeUrl}` };
    }
    return { status: "ok", message: "Gerrit plugin configured and ready" };
  },
});

export default plugin;
runWorker(plugin, import.meta.url);
