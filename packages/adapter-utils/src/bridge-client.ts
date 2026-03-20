/**
 * Bridge client for calling the ai_tools_bridge Python sidecar.
 *
 * Plugin workers use this to:
 *  1. Fetch the tool manifest from the bridge at setup time.
 *  2. Execute individual tools by forwarding params + resolved credentials.
 *
 * @example
 * ```ts
 * const bridge = createBridgeClient("http://ai-tools-bridge:8000", "jira");
 * const tools = await bridge.getToolManifest();
 * const result = await bridge.execute("get_jira_issue", { key: "PROJ-1" }, { token: "..." });
 * ```
 */

// ---------------------------------------------------------------------------
// Types mirrored from the bridge's Pydantic response models
// ---------------------------------------------------------------------------

export interface BridgeToolManifestEntry {
  /** Package slug: "github" | "jira" | "confluence" | "gerrit" */
  package: string;
  /** Snake-case tool name, e.g. "get_jira_issue" */
  name: string;
  /** Fully-qualified name: "{package}.{name}" */
  full_name: string;
  /** Human-readable title */
  display_name: string;
  /** Tool description forwarded to the agent */
  description: string;
  /** JSON Schema object for the tool's parameters */
  parameters_schema: Record<string, unknown>;
  /** "low" | "medium" | "high" */
  risk_level: "low" | "medium" | "high";
}

export interface BridgeManifestResponse {
  tools: BridgeToolManifestEntry[];
}

export interface BridgeExecuteRequest {
  params: Record<string, unknown>;
  credentials: Record<string, unknown>;
}

export interface BridgeToolResult {
  content?: string;
  data?: unknown;
  error?: string;
}

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export class BridgeError extends Error {
  constructor(
    message: string,
    public readonly statusCode?: number,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = "BridgeError";
  }
}

// ---------------------------------------------------------------------------
// Client factory
// ---------------------------------------------------------------------------

export interface BridgeClient {
  /** Fetch the manifest for this client's package (or all if package is omitted). */
  getToolManifest(): Promise<BridgeToolManifestEntry[]>;
  /** Execute a tool by name with the given params and credentials. */
  execute(
    toolName: string,
    params: Record<string, unknown>,
    credentials: Record<string, unknown>,
  ): Promise<BridgeToolResult>;
  /** Check bridge health. Returns true if reachable. */
  isHealthy(): Promise<boolean>;
}

/**
 * Create a bridge client for a specific ai_tools_* package.
 *
 * @param baseUrl - Base URL of the bridge server, e.g. "http://ai-tools-bridge:8000"
 * @param packageSlug - One of "github" | "jira" | "confluence" | "gerrit"
 * @param options - Optional fetch options (e.g. custom headers, timeout signal)
 */
export function createBridgeClient(
  baseUrl: string,
  packageSlug: string,
  options: { headers?: Record<string, string>; timeoutMs?: number } = {},
): BridgeClient {
  const { headers: extraHeaders = {}, timeoutMs = 30_000 } = options;

  function buildHeaders(): Record<string, string> {
    return {
      "Content-Type": "application/json",
      ...extraHeaders,
    };
  }

  function buildSignal(): AbortSignal {
    return AbortSignal.timeout(timeoutMs);
  }

  async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
    let res: Response;
    try {
      res = await fetch(url, { signal: buildSignal(), ...init });
    } catch (err) {
      throw new BridgeError(`Bridge request failed: ${(err as Error).message}`);
    }
    if (!res.ok) {
      let body: unknown;
      try {
        body = await res.json();
      } catch {
        body = await res.text();
      }
      throw new BridgeError(
        `Bridge returned HTTP ${res.status} for ${url}`,
        res.status,
        body,
      );
    }
    return res.json() as Promise<T>;
  }

  return {
    async getToolManifest(): Promise<BridgeToolManifestEntry[]> {
      const url = `${baseUrl}/tools/manifest/${packageSlug}`;
      const resp = await fetchJSON<BridgeManifestResponse>(url, {
        headers: buildHeaders(),
      });
      return resp.tools;
    },

    async execute(
      toolName: string,
      params: Record<string, unknown>,
      credentials: Record<string, unknown>,
    ): Promise<BridgeToolResult> {
      const url = `${baseUrl}/tools/${packageSlug}/${toolName}`;
      const body: BridgeExecuteRequest = { params, credentials };
      return fetchJSON<BridgeToolResult>(url, {
        method: "POST",
        headers: buildHeaders(),
        body: JSON.stringify(body),
      });
    },

    async isHealthy(): Promise<boolean> {
      try {
        const url = `${baseUrl}/health`;
        await fetchJSON<unknown>(url, { headers: buildHeaders() });
        return true;
      } catch {
        return false;
      }
    },
  };
}
