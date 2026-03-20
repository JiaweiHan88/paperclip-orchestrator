# AI-Tools → Paperclip Plugin Integration Plan

**Date:** 2026-03-20
**Status:** Implemented ✅
**Author:** @JiaweiHan88

---

## 1. Context

Four Python MCP tool packages have been added to the repository root:

| Folder | Python Package | Tools (count) | Risk Levels |
|---|---|---|---|
| `ai_tools_github/` | `ai-tools-github` | 28 | LOW / MEDIUM / HIGH |
| `ai_tools_jira/` | `ai-tools-jira` | 11 | LOW / MEDIUM / HIGH |
| `ai_tools_confluence/` | `ai-tools-confluence` | 12 | LOW / MEDIUM / HIGH |
| `ai_tools_gerrit/` | `ai-tools-gerrit` | 20+ | LOW / MEDIUM / HIGH |

Each package follows the same pattern:
- **`tools.py`** — Exports `ToolDescription` instances (name, description, args schema from Pydantic `BaseModel`, risk level, handler function)
- **`instance.py`** — Creates an authenticated client (JIRA client, GitHub GraphQL client, Gerrit REST client, Confluence REST client)
- **Individual modules** — One `.py` file per tool (e.g. `issue.py`, `search.py`) with a Pydantic input model and an async handler function

The Paperclip plugin framework already has **skeleton TypeScript plugins** in:
- `packages/plugins/examples/plugin-github/`
- `packages/plugins/examples/plugin-jira/`
- `packages/plugins/examples/plugin-confluence/`
- `packages/plugins/examples/plugin-gerrit/`

These skeletons have proper manifests, event/job/webhook scaffolding, and `// TODO` placeholders for tool registration via `ctx.tools.register()`. The goal is to **bridge the existing Python tool implementations into these TypeScript plugin workers** so agents can invoke them through the Paperclip plugin tool system.

---

## 2. Architecture Options

### Option A — Python Sidecar (Recommended)

```
┌────────────────────────────────────┐
│  Paperclip Server (Node.js)        │
│  ├─ Plugin Host                    │
│  │  ├─ plugin-github worker.ts     │──── JSON-RPC ────┐
│  │  ├─ plugin-jira worker.ts       │──── JSON-RPC ────┤
│  │  ├─ plugin-confluence worker.ts │──── JSON-RPC ────┤
│  │  └─ plugin-gerrit worker.ts     │──── JSON-RPC ────┤
│  └─ PluginToolDispatcher           │                   │
└────────────────────────────────────┘                   │
                                                         ▼
                                            ┌───────────────────────┐
                                            │  Python Sidecar       │
                                            │  (FastAPI / stdio)    │
                                            │  ├─ ai_tools_github   │
                                            │  ├─ ai_tools_jira     │
                                            │  ├─ ai_tools_confluence│
                                            │  └─ ai_tools_gerrit   │
                                            └───────────────────────┘
```

Each TS plugin worker calls out to a Python sidecar process (HTTP or stdio JSON-RPC) that wraps the existing Python tool functions. This avoids rewriting ~70 tool implementations in TypeScript.

### Option B — TypeScript Native Rewrite

Rewrite each Python tool as a TypeScript function inside the plugin worker, calling GitHub GraphQL / Jira REST / Confluence REST / Gerrit REST directly. Higher effort, but zero Python dependency.

### Option C — Hybrid

Use the Python sidecar for complex tools (batch analysis, template rendering, GraphQL queries), rewrite simple REST-call tools in TypeScript natively.

**Recommendation:** Start with **Option A** (Python sidecar) for maximum reuse, then migrate high-traffic tools to native TypeScript (Option C) based on latency/reliability data.

---

## 3. Implementation Phases

### Phase 1 — Python Tool Bridge Server

**Goal:** Expose all `ai_tools_*` functions over a uniform HTTP/JSON-RPC interface.

| Step | Task | Files |
|---|---|---|
| 1.1 | Create `ai_tools_bridge/` package at repo root | `ai_tools_bridge/` |
| 1.2 | Build a FastAPI app that auto-discovers tools from each `ai_tools_*` package's `tools.py` | `ai_tools_bridge/src/server.py` |
| 1.3 | For each `ToolDescription`, expose: `POST /tools/{package}/{tool_name}` | |
| 1.4 | Auto-generate JSON Schema from Pydantic input models (`model.model_json_schema()`) | |
| 1.5 | Map `RiskLevel` → Paperclip tool metadata (`riskLevel: "low" | "medium" | "high"`) | |
| 1.6 | Handle instance/client injection (read credentials from env vars or plugin config passed in request body) | |
| 1.7 | Add `GET /tools/manifest` endpoint that returns all tool declarations (name, description, JSON Schema) for each package | |
| 1.8 | Add health check `GET /health` | |
| 1.9 | Dockerfile for the bridge (`python:3.12-slim`, install all 4 packages) | |
| 1.10 | Docker Compose service alongside Paperclip server | `docker-compose.yml` |

**Schema translation example:**

```python
# Python (Pydantic)
class JiraIssueInput(BaseModel):
    key: str = Field(description="The key of the Jira issue")
    fields: list[str] | None = Field(default=None)
```

```json
// Auto-generated JSON Schema → plugin parametersSchema
{
  "type": "object",
  "properties": {
    "key": { "type": "string", "description": "The key of the Jira issue" },
    "fields": {
      "anyOf": [{ "type": "array", "items": { "type": "string" } }, { "type": "null" }],
      "default": null
    }
  },
  "required": ["key"]
}
```

### Phase 2 — Wire Plugin Workers to Bridge

**Goal:** Each skeleton plugin worker calls the Python bridge instead of `// TODO`.

| Step | Task | Files |
|---|---|---|
| 2.1 | Add `TOOL_NAMES` constants mapping tool names for each plugin | `plugin-*/src/constants.ts` |
| 2.2 | Create a shared `bridge-client.ts` utility in plugin SDK or adapter-utils that calls the Python bridge | `packages/adapter-utils/src/bridge-client.ts` |
| 2.3 | In each plugin `worker.ts setup()`, fetch tool manifest from bridge at startup | `plugin-*/src/worker.ts` |
| 2.4 | Register each tool via `ctx.tools.register(name, declaration, handler)` where handler proxies to bridge | |
| 2.5 | Pass plugin instance config (credentials, base URLs) into bridge call body | |
| 2.6 | Map bridge response → `ToolResult { content, data, error }` | |
| 2.7 | Wire `RiskLevel` from bridge manifest into tool metadata | |

**Worker registration example (after):**

```typescript
// plugin-jira/src/worker.ts
import { createBridgeClient } from "@paperclipai/adapter-utils";

async setup(ctx) {
  const config = await getConfig(ctx);
  const bridge = createBridgeClient("http://bridge:8000", "jira");

  // Auto-discover tools from bridge
  const tools = await bridge.getToolManifest();

  for (const tool of tools) {
    ctx.tools.register(tool.name, {
      displayName: tool.displayName,
      description: tool.description,
      parametersSchema: tool.parametersSchema,
    }, async (params, runCtx) => {
      const secret = await ctx.secrets.resolve(config.jiraTokenSecretRef);
      return bridge.execute(tool.name, params, {
        baseUrl: config.jiraBaseUrl,
        token: secret,
        userEmail: config.jiraUserEmail,
      });
    });
  }
}
```

### Phase 3 — Update Manifests & Constants

**Goal:** Plugin manifests accurately declare all tools so the host can validate capabilities.

| Step | Task | Files |
|---|---|---|
| 3.1 | Add `tools` array to each plugin's `manifest.ts` with entries from bridge | `plugin-*/src/manifest.ts` |
| 3.2 | Populate `TOOL_NAMES` in `constants.ts` from the bridge manifest (or hardcode for type safety) | `plugin-*/src/constants.ts` |
| 3.3 | Ensure `"agent.tools.register"` capability is listed (already present) | |
| 3.4 | Add `"http.outbound"` capability if missing (needed for bridge calls) | |

### Phase 4 — Credential Flow

**Goal:** Plugin instance config → secrets → Python bridge credentials.

| Step | Task | Files |
|---|---|---|
| 4.1 | Define `instanceConfigSchema` for each plugin (already partially done) with fields for base URL, token secret ref, user email | `plugin-*/src/manifest.ts` |
| 4.2 | Resolve secret refs via `ctx.secrets.resolve()` in worker before passing to bridge | `plugin-*/src/worker.ts` |
| 4.3 | Bridge server accepts credentials per-request (no env var state) — stateless execution | `ai_tools_bridge/src/server.py` |
| 4.4 | Document configuration steps in each plugin's `README.md` | `plugin-*/README.md` |

### Phase 5 — Testing

| Step | Task | Files |
|---|---|---|
| 5.1 | Unit tests for bridge server (mock external APIs, test schema generation) | `ai_tools_bridge/tests/` |
| 5.2 | Unit tests for bridge-client in TypeScript | `packages/adapter-utils/src/__tests__/` |
| 5.3 | Integration test: plugin worker → bridge → mock external API | `tests/e2e/plugin-tools/` |
| 5.4 | Use `createTestHarness()` from plugin SDK to test tool registration | `plugin-*/src/__tests__/` |
| 5.5 | Verify per-agent plugin overrides correctly hide tools | |

### Phase 6 — Dev Experience

| Step | Task |
|---|---|
| 6.1 | Add `pnpm dev` script that also starts the Python bridge (`uv run ai_tools_bridge`) |
| 6.2 | Add bridge URL to `.env.example` (`AI_TOOLS_BRIDGE_URL=http://localhost:8000`) |
| 6.3 | Update `doc/DEVELOPING.md` with bridge setup instructions |
| 6.4 | Add bridge service to `docker-compose.yml` and `docker-compose.quickstart.yml` |

---

## 4. Tool Inventory

### GitHub (28 tools)

| Tool | Risk | Description |
|---|---|---|
| `get-pull-request-diff` | LOW | Get diff for a pull request |
| `get-commit-diff` | LOW | Get diff for a commit |
| `batch-analyze-pull-request` | LOW | Analyze multiple PRs |
| `get-pull-requests-between-commits` | LOW | List PRs between two commits |
| `get-pull-request` | LOW | Get PR details |
| `search-pull-requests` | LOW | Search PRs |
| `get-issue-time-line` | LOW | Get issue timeline |
| `get-issues-from-project-board` | LOW | List filtered board issues |
| `get-project-fields` | LOW | Get project field definitions |
| `get-repo-history` | LOW | Get repo commit history |
| `get-repo-stats` | LOW | Get repo statistics |
| `get-repo-tree` | LOW | Get repo file tree |
| `get-file-content` | LOW | Read file from repo |
| `get-zuul-buildsets-for-pr` | LOW | Get CI buildsets |
| `get-pull-request-structured` | LOW | Get structured PR data |
| `get-pull-request-state` | LOW | Get PR status |
| `get-repo-folder-files-path` | LOW | List files in folder |
| `search-code` | LOW | Search code in repos |
| `update-pull-request-description` | HIGH | Update PR description |
| `inject-to-pull-request-description` | HIGH | Append to PR description |
| `add-comment-to-pull-request` | MEDIUM | Comment on PR |
| `add-label-to-pull-request` | MEDIUM | Add label to PR |
| `remove-label-from-pull-request` | MEDIUM | Remove label from PR |
| `create-reaction-to-pr-comment` | MEDIUM | React to PR comment |
| `create-branch` | HIGH | Create a branch |
| `create-commit-on-branch` | HIGH | Commit files to branch |
| `create-pull-request` | HIGH | Open a pull request |
| `create-issue` | HIGH | Create an issue |

### Jira (11 tools)

| Tool | Risk | Description |
|---|---|---|
| `get-jira-issue` | LOW | Fetch issue details |
| `download-jira-attachment` | LOW | Download attachment |
| `search-jira` | LOW | JQL search |
| `get-jira-pull-requests` | LOW | Get linked PRs |
| `get-jira-fields` | LOW | Discover available fields |
| `get-jira-transitions` | LOW | Get workflow transitions |
| `create-jira-ticket` | MEDIUM | Create a ticket |
| `update-jira-ticket` | HIGH | Update a ticket |
| `add-jira-comment` | MEDIUM | Add comment |
| `transition-jira-issue` | MEDIUM | Change issue status |
| `link-jira-issues` | MEDIUM | Link two issues |

### Confluence (12 tools)

| Tool | Risk | Description |
|---|---|---|
| `get-page-by-id` | LOW | Fetch page by ID |
| `get-page-by-title` | LOW | Fetch page by title |
| `get-page-by-id-html` | LOW | Fetch raw HTML by ID |
| `get-page-by-title-html` | LOW | Fetch raw HTML by title |
| `search-cql` | LOW | CQL search |
| `search-freetext` | LOW | Free-text search |
| `get-spaces` | LOW | List spaces |
| `get-page-tree` | LOW | Page hierarchy |
| `update-page` | HIGH | Update page content |
| `create-page` | MEDIUM | Create new page |
| `add-comment` | MEDIUM | Comment on page |
| `relocate-page` | HIGH | Move/copy page |

### Gerrit (20+ tools)

| Tool | Risk | Description |
|---|---|---|
| `query-changes` | LOW | Search changes |
| `query-changes-by-date` | LOW | Date-filtered search |
| `get-most-recent-cl` | LOW | Latest change |
| `get-change-details` | LOW | Change metadata |
| `changes-submitted-together` | LOW | Related changes |
| `list-change-comments` | LOW | List review comments |
| `get-commit-message` | LOW | Commit message text |
| `get-bugs-from-cl` | LOW | Extract bug references |
| `get-file-content` | LOW | Read file at revision |
| `list-change-files` | LOW | Files in a change |
| `get-change-diff` | LOW | Full change diff |
| `get-file-diff` | LOW | Single file diff |
| `get-project-branches` | LOW | List branches |
| `suggest-reviewers` | LOW | Suggest reviewers |
| `create-change` | HIGH | Create a new change |
| `abandon-change` | HIGH | Abandon a change |
| `revert-change` | HIGH | Revert a change |
| `revert-submission` | HIGH | Revert a submission |
| `set-topic` | MEDIUM | Set change topic |
| `set-work-in-progress` | MEDIUM | Mark WIP |
| `set-ready-for-review` | MEDIUM | Mark ready |
| `add-reviewer` | MEDIUM | Add reviewer |
| `set-review` | HIGH | Submit review scores |
| `post-review-comment` | MEDIUM | Post inline comment |

---

## 5. Risk-Level → Approval Gate Mapping

The Python tools already have `RiskLevel` annotations. These map directly to Paperclip's governance model:

| RiskLevel | Paperclip Behavior |
|---|---|
| `LOW` | Agent can execute freely |
| `MEDIUM` | Agent can execute; logged in activity feed |
| `HIGH` | Requires approval gate (if company governance is enabled) |

This aligns with the `doc/SPEC-implementation.md` approval gate system.

---

## 6. File Impact Summary

### New files

| File | Purpose |
|---|---|
| `ai_tools_bridge/` | Python FastAPI bridge server |
| `ai_tools_bridge/src/server.py` | Main bridge app |
| `ai_tools_bridge/src/registry.py` | Auto-discover tools from packages |
| `ai_tools_bridge/Dockerfile` | Docker image for bridge |
| `ai_tools_bridge/pyproject.toml` | Python package config |
| `packages/adapter-utils/src/bridge-client.ts` | TS client for calling bridge |

### Modified files

| File | Change |
|---|---|
| `packages/plugins/examples/plugin-github/src/worker.ts` | Add tool registration via bridge |
| `packages/plugins/examples/plugin-github/src/constants.ts` | Populate `TOOL_NAMES` |
| `packages/plugins/examples/plugin-github/src/manifest.ts` | Add tool declarations |
| `packages/plugins/examples/plugin-jira/src/worker.ts` | Add tool registration via bridge |
| `packages/plugins/examples/plugin-jira/src/constants.ts` | Populate `TOOL_NAMES` |
| `packages/plugins/examples/plugin-jira/src/manifest.ts` | Add tool declarations |
| `packages/plugins/examples/plugin-confluence/src/worker.ts` | Add tool registration via bridge |
| `packages/plugins/examples/plugin-confluence/src/constants.ts` | Populate `TOOL_NAMES` |
| `packages/plugins/examples/plugin-confluence/src/manifest.ts` | Add tool declarations |
| `packages/plugins/examples/plugin-gerrit/src/worker.ts` | Add tool registration via bridge |
| `packages/plugins/examples/plugin-gerrit/src/constants.ts` | Populate `TOOL_NAMES` |
| `packages/plugins/examples/plugin-gerrit/src/manifest.ts` | Add tool declarations |
| `docker-compose.yml` | Add bridge service |
| `docker-compose.quickstart.yml` | Add bridge service |
| `scripts/dev-runner.mjs` | Start bridge alongside server |
| `doc/DEVELOPING.md` | Bridge setup docs |

---

## 7. Open Questions

1. **Stdio vs HTTP for bridge?** — HTTP is simpler for Docker networking; stdio JSON-RPC is lighter for single-host dev. Could support both.
2. **Schema drift** — When Python tool schemas change, the TS manifests need updating. Should we auto-generate manifests from the bridge's `/tools/manifest` endpoint at build time?
3. **Credential isolation** — The bridge receives credentials per-request. Should we add mTLS or at least require a shared secret between server and bridge?
4. **Performance** — Python cold start for some tools (GitHub GraphQL, Jira client init). Should the bridge keep warm client pools keyed by credential hash?
5. **Native migration priority** — Which tools should be rewritten in TypeScript first? Candidates: simple REST-GET tools (Jira issue fetch, Confluence page fetch).

---

## 8. Success Criteria

- [x] All 70+ tools from `ai_tools_*` are registerable as Paperclip plugin tools
- [x] Agents can discover tools via `PluginToolDispatcher.listTools()`
- [x] Agents can execute tools and receive structured `ToolResult` responses
- [x] Per-agent plugin overrides (from our earlier work) correctly filter available tools
- [x] Tool risk levels map to the approval gate system
- [x] `pnpm dev` starts both the Node server and the Python bridge
- [x] Docker Compose brings up the full stack including the bridge
- [x] Plugin health endpoints report bridge connectivity
