import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createTestHarness } from "@paperclipai/plugin-sdk/testing";
import manifest from "../manifest.js";
import plugin from "../worker.js";
import type { BridgeManifestResponse, BridgeToolResult } from "@paperclipai/adapter-utils";

// Convenience aliases: access the plugin lifecycle via `plugin.definition`
const setup = (ctx: Parameters<typeof plugin.definition.setup>[0]) =>
  plugin.definition.setup(ctx);
const onHealth = () => plugin.definition.onHealth!();

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const BRIDGE_URL = "http://test-bridge:8000";

/** Build a minimal manifest entry for testing. */
function makeManifestResponse(toolNames: string[] = ["get_jira_issue"]): BridgeManifestResponse {
  return {
    tools: toolNames.map((name) => ({
      package: "jira",
      name,
      full_name: `jira.${name}`,
      display_name: name.replace(/_/g, " "),
      description: `Test tool: ${name}`,
      parameters_schema: {
        type: "object" as const,
        properties: { key: { type: "string" } },
      },
      risk_level: "low" as const,
    })),
  };
}

function makeToolResult(overrides: Partial<BridgeToolResult> = {}): BridgeToolResult {
  return { content: "mock result", ...overrides };
}

/** Returns a Response-like mock for fetch. */
function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("plugin-jira worker", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    process.env.AI_TOOLS_BRIDGE_URL = BRIDGE_URL;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    delete process.env.AI_TOOLS_BRIDGE_URL;
  });

  // -------------------------------------------------------------------------
  // setup() — bridge available
  // -------------------------------------------------------------------------

  describe("setup() with bridge available", () => {
    it("registers tools returned by the bridge manifest", async () => {
      fetchMock.mockResolvedValueOnce(jsonResponse(makeManifestResponse(["get_jira_issue", "search_jira"])));

      const harness = createTestHarness({
        manifest,
        config: {
          jiraBaseUrl: "https://jira.example.com",
          jiraTokenSecretRef: "ref:jira-token",
          jiraUserEmail: "bot@example.com",
        },
      });

      await setup(harness.ctx);

      // Both tools should now be registered — executeTool won't throw 
      // "Tool not found" if they're registered. We confirm by calling one.
      fetchMock.mockResolvedValueOnce(jsonResponse(makeToolResult({ content: "issue details" })));
      const result = await harness.executeTool("get_jira_issue", { key: "PROJ-1" });
      expect(result).toMatchObject({ content: "issue details" });
    });

    it("hits /tools/manifest/jira on the configured bridge URL", async () => {
      fetchMock.mockResolvedValueOnce(jsonResponse(makeManifestResponse()));

      const harness = createTestHarness({ manifest, config: { jiraBaseUrl: "https://jira.example.com" } });
      await setup(harness.ctx);

      const [manifestUrl] = fetchMock.mock.calls[0] as [string, RequestInit?];
      expect(manifestUrl).toBe(`${BRIDGE_URL}/tools/manifest/jira`);
    });

    it("injects jira_base_url and resolved token into bridge execute call", async () => {
      fetchMock
        .mockResolvedValueOnce(jsonResponse(makeManifestResponse(["get_jira_issue"])))
        .mockResolvedValueOnce(jsonResponse(makeToolResult()));

      const harness = createTestHarness({
        manifest,
        config: {
          jiraBaseUrl: "https://jira.example.com",
          jiraTokenSecretRef: "ref:jira-token",
          jiraUserEmail: "bot@example.com",
        },
      });

      await setup(harness.ctx);
      await harness.executeTool("get_jira_issue", { key: "PROJ-42" });

      // The second fetch call is the execute POST
      const [execUrl, execInit] = fetchMock.mock.calls[1] as [string, RequestInit?];
      expect(execUrl).toBe(`${BRIDGE_URL}/tools/jira/get_jira_issue`);

      const body = JSON.parse(execInit?.body as string);
      expect(body.params).toEqual({ key: "PROJ-42" });
      expect(body.credentials.jira_base_url).toBe("https://jira.example.com");
      // ctx.secrets.resolve returns "resolved:<ref>" in test harness
      expect(body.credentials.token).toBe("resolved:ref:jira-token");
      expect(body.credentials.user_email).toBe("bot@example.com");
    });

    it("returns error field from bridge result without throwing", async () => {
      fetchMock
        .mockResolvedValueOnce(jsonResponse(makeManifestResponse(["get_jira_issue"])))
        .mockResolvedValueOnce(jsonResponse(makeToolResult({ error: "Issue PROJ-99 not found" })));

      const harness = createTestHarness({ manifest, config: { jiraBaseUrl: "https://jira.example.com" } });
      await setup(harness.ctx);

      const result = await harness.executeTool("get_jira_issue", { key: "PROJ-99" });
      expect(result).toMatchObject({ error: "Issue PROJ-99 not found" });
    });

    it("logs tool registration count at info level", async () => {
      fetchMock.mockResolvedValueOnce(
        jsonResponse(makeManifestResponse(["get_jira_issue", "search_jira", "create_jira_ticket"])),
      );

      const harness = createTestHarness({ manifest, config: { jiraBaseUrl: "https://jira.example.com" } });
      await setup(harness.ctx);

      const infoLogs = harness.logs.filter((l) => l.level === "info");
      const registrationLog = infoLogs.find((l) => l.message.includes("registered tools"));
      expect(registrationLog).toBeDefined();
      expect(registrationLog?.meta?.count).toBe(3);
    });
  });

  // -------------------------------------------------------------------------
  // setup() — bridge unavailable
  // -------------------------------------------------------------------------

  describe("setup() when bridge is unreachable", () => {
    it("does not throw — setup completes with a warning log", async () => {
      fetchMock.mockRejectedValueOnce(new TypeError("ECONNREFUSED"));

      const harness = createTestHarness({ manifest, config: { jiraBaseUrl: "https://jira.example.com" } });
      // Must not throw
      await expect(setup(harness.ctx)).resolves.not.toThrow();

      const warnLogs = harness.logs.filter((l) => l.level === "warn");
      expect(warnLogs.some((l) => l.message.includes("bridge unavailable"))).toBe(true);
    });
  });

  // -------------------------------------------------------------------------
  // onHealth()
  // -------------------------------------------------------------------------

  describe("onHealth()", () => {
    it("returns ok when bridge is healthy and plugin is configured", async () => {
      // Setup: bridge manifest fetch
      fetchMock
        .mockResolvedValueOnce(jsonResponse(makeManifestResponse()))
        // onHealth: bridge /health probe
        .mockResolvedValueOnce(jsonResponse({ status: "ok" }));

      const harness = createTestHarness({
        manifest,
        config: {
          jiraBaseUrl: "https://jira.example.com",
          jiraTokenSecretRef: "ref:token",
        },
      });

      await setup(harness.ctx);
      const health = await onHealth();
      expect(health.status).toBe("ok");
    });

    it("returns degraded when bridge is unreachable", async () => {
      // Setup: bridge manifest fetch fails (skips registration)
      fetchMock
        .mockRejectedValueOnce(new TypeError("ECONNREFUSED"))
        // onHealth: bridge /health probe also fails
        .mockRejectedValueOnce(new TypeError("ECONNREFUSED"));

      const harness = createTestHarness({
        manifest,
        config: {
          jiraBaseUrl: "https://jira.example.com",
          jiraTokenSecretRef: "ref:token",
        },
      });

      await setup(harness.ctx);
      const health = await onHealth();
      expect(health.status).toBe("degraded");
      expect(health.message).toContain("bridge");
    });

    it("returns degraded when jiraBaseUrl is not configured", async () => {
      // Bridge up, but no config
      fetchMock
        .mockResolvedValueOnce(jsonResponse(makeManifestResponse()))
        .mockResolvedValueOnce(jsonResponse({ status: "ok" }));

      const harness = createTestHarness({ manifest, config: {} });
      await setup(harness.ctx);
      const health = await onHealth();
      expect(health.status).toBe("degraded");
      expect(health.message).toContain("not configured");
    });
  });
});
