import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  createBridgeClient,
  BridgeError,
  type BridgeToolManifestEntry,
  type BridgeToolResult,
} from "../bridge-client.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeManifestEntry(
  overrides: Partial<BridgeToolManifestEntry> = {},
): BridgeToolManifestEntry {
  return {
    package: "jira",
    name: "get_jira_issue",
    full_name: "jira.get_jira_issue",
    display_name: "Get Jira Issue",
    description: "Fetch details of a Jira issue.",
    parameters_schema: { type: "object", properties: { key: { type: "string" } } },
    risk_level: "low",
    ...overrides,
  };
}

function makeResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("createBridgeClient", () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // -------------------------------------------------------------------------
  // getToolManifest()
  // -------------------------------------------------------------------------

  describe("getToolManifest()", () => {
    it("fetches manifest from /tools/manifest/{package} and returns tools array", async () => {
      const entry = makeManifestEntry();
      fetchSpy.mockResolvedValueOnce(makeResponse({ tools: [entry] }));

      const client = createBridgeClient("http://bridge:8000", "jira");
      const tools = await client.getToolManifest();

      expect(tools).toHaveLength(1);
      expect(tools[0]).toEqual(entry);

      const [url] = fetchSpy.mock.calls[0] as [string, RequestInit?];
      expect(url).toBe("http://bridge:8000/tools/manifest/jira");
    });

    it("includes Content-Type header in the request", async () => {
      fetchSpy.mockResolvedValueOnce(makeResponse({ tools: [] }));

      const client = createBridgeClient("http://bridge:8000", "jira");
      await client.getToolManifest();

      const [, init] = fetchSpy.mock.calls[0] as [string, RequestInit?];
      expect((init?.headers as Record<string, string>)?.["Content-Type"]).toBe(
        "application/json",
      );
    });

    it("passes extra headers when provided", async () => {
      fetchSpy.mockResolvedValueOnce(makeResponse({ tools: [] }));

      const client = createBridgeClient("http://bridge:8000", "jira", {
        headers: { "X-Custom": "value" },
      });
      await client.getToolManifest();

      const [, init] = fetchSpy.mock.calls[0] as [string, RequestInit?];
      expect((init?.headers as Record<string, string>)?.["X-Custom"]).toBe("value");
    });

    it("throws BridgeError on non-ok HTTP response", async () => {
      fetchSpy.mockResolvedValueOnce(
        makeResponse({ detail: "Not found" }, 404),
      );

      const client = createBridgeClient("http://bridge:8000", "jira");
      await expect(client.getToolManifest()).rejects.toThrow(BridgeError);
    });

    it("includes the HTTP status code in BridgeError", async () => {
      fetchSpy.mockResolvedValueOnce(makeResponse({ detail: "error" }, 500));

      const client = createBridgeClient("http://bridge:8000", "jira");
      let err: BridgeError | undefined;
      try {
        await client.getToolManifest();
      } catch (e) {
        err = e as BridgeError;
      }
      expect(err).toBeInstanceOf(BridgeError);
      expect(err?.statusCode).toBe(500);
    });

    it("throws BridgeError on network failure", async () => {
      fetchSpy.mockRejectedValueOnce(new TypeError("Failed to fetch"));

      const client = createBridgeClient("http://bridge:8000", "jira");
      await expect(client.getToolManifest()).rejects.toThrow(BridgeError);
    });
  });

  // -------------------------------------------------------------------------
  // execute()
  // -------------------------------------------------------------------------

  describe("execute()", () => {
    it("POSTs to /tools/{package}/{toolName} with params and credentials", async () => {
      const result: BridgeToolResult = { content: "PROJ-1 details" };
      fetchSpy.mockResolvedValueOnce(makeResponse(result));

      const client = createBridgeClient("http://bridge:8000", "jira");
      const output = await client.execute(
        "get_jira_issue",
        { key: "PROJ-1" },
        { token: "secret", jira_base_url: "https://jira.example.com" },
      );

      expect(output).toEqual(result);

      const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit?];
      expect(url).toBe("http://bridge:8000/tools/jira/get_jira_issue");
      expect(init?.method).toBe("POST");

      const body = JSON.parse(init?.body as string);
      expect(body.params).toEqual({ key: "PROJ-1" });
      expect(body.credentials).toEqual({
        token: "secret",
        jira_base_url: "https://jira.example.com",
      });
    });

    it("throws BridgeError on 422 validation error from bridge", async () => {
      fetchSpy.mockResolvedValueOnce(
        makeResponse({ detail: "Validation error" }, 422),
      );

      const client = createBridgeClient("http://bridge:8000", "jira");
      await expect(
        client.execute("get_jira_issue", {}, {}),
      ).rejects.toThrow(BridgeError);
    });

    it("propagates error field from a successful bridge response", async () => {
      const result: BridgeToolResult = { error: "Issue not found" };
      fetchSpy.mockResolvedValueOnce(makeResponse(result));

      const client = createBridgeClient("http://bridge:8000", "jira");
      const output = await client.execute("get_jira_issue", { key: "MISSING" }, {});

      // Bridge returning an error in the result body is NOT a BridgeError —
      // the HTTP call succeeded; the tool itself failed.
      expect(output.error).toBe("Issue not found");
    });
  });

  // -------------------------------------------------------------------------
  // isHealthy()
  // -------------------------------------------------------------------------

  describe("isHealthy()", () => {
    it("returns true when /health responds with 200", async () => {
      fetchSpy.mockResolvedValueOnce(makeResponse({ status: "ok" }));

      const client = createBridgeClient("http://bridge:8000", "jira");
      expect(await client.isHealthy()).toBe(true);

      const [url] = fetchSpy.mock.calls[0] as [string, RequestInit?];
      expect(url).toBe("http://bridge:8000/health");
    });

    it("returns false when /health returns a non-ok HTTP status", async () => {
      fetchSpy.mockResolvedValueOnce(makeResponse({ error: "unhealthy" }, 503));

      const client = createBridgeClient("http://bridge:8000", "jira");
      expect(await client.isHealthy()).toBe(false);
    });

    it("returns false when fetch throws (network error)", async () => {
      fetchSpy.mockRejectedValueOnce(new TypeError("ECONNREFUSED"));

      const client = createBridgeClient("http://bridge:8000", "jira");
      expect(await client.isHealthy()).toBe(false);
    });

    it("uses the base URL from the factory, not the package slug", async () => {
      fetchSpy.mockResolvedValueOnce(makeResponse({ status: "ok" }));

      const client = createBridgeClient("http://custom-host:9000", "gerrit");
      await client.isHealthy();

      const [url] = fetchSpy.mock.calls[0] as [string, RequestInit?];
      expect(url).toBe("http://custom-host:9000/health");
    });
  });

  // -------------------------------------------------------------------------
  // BridgeError
  // -------------------------------------------------------------------------

  describe("BridgeError", () => {
    it("has name BridgeError", () => {
      const err = new BridgeError("test");
      expect(err.name).toBe("BridgeError");
    });

    it("stores statusCode and body", () => {
      const err = new BridgeError("test", 404, { detail: "not found" });
      expect(err.statusCode).toBe(404);
      expect(err.body).toEqual({ detail: "not found" });
    });

    it("is an instance of Error", () => {
      expect(new BridgeError("x")).toBeInstanceOf(Error);
    });
  });
});
