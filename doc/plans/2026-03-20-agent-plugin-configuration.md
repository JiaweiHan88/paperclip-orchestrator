# Agent Plugin & Tool Configuration Tab

**Date:** 2026-03-20
**Status:** Plan
**Route:** `/:companyPrefix/agents/:agentRef/plugins`

## 1. Summary

Add a new **"Plugins"** tab to every agent's detail page. The tab provides:

1. A **toggle for each installed plugin** — enable or disable it per agent.
2. A **force-directed graph visualisation** — the agent is centred; connected plugins radiate outward; each plugin node expands to show its tools.
3. **Per-tool toggles** — click a tool to enable/disable it for this agent.

The result: operators can precisely control which plugins and tools each agent can use, without affecting other agents.

---

## 2. Current State

| Concept | Today | Location |
|---|---|---|
| Plugin install | Instance-wide, `plugins` table has no `company_id` or `agent_id` | `packages/db/src/schema/plugins.ts` |
| Company scoping | `plugin_company_settings` allows per-company enable/disable | `packages/db/src/schema/plugin_company_settings.ts` |
| Agent scoping | **Does not exist** — no `agent_plugin_settings` or `agent_tool_overrides` table | — |
| Tool dispatch | `PluginToolDispatcher.listToolsForAgent()` returns **all** tools from ready plugins; no per-agent filtering | `server/src/services/plugin-tool-dispatcher.ts` |
| Agent detail tabs | `dashboard`, `configuration`, `skills` (commented out), `runs`, `budget` | `ui/src/pages/AgentDetail.tsx:190` |
| Plugin tools API | `GET /api/plugins/tools` lists all tools; `POST /api/plugins/tools/execute` executes | `server/src/routes/plugins.ts:485+` |
| Graph lib | None currently in `ui/package.json` | — |

---

## 3. Data Model

### 3.1 New table: `agent_plugin_overrides`

```
packages/db/src/schema/agent_plugin_overrides.ts
```

```sql
CREATE TABLE agent_plugin_overrides (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id        uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  plugin_id       uuid NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
  enabled         boolean NOT NULL DEFAULT true,
  -- null = all tools enabled; non-null = only listed tools enabled
  tool_overrides  jsonb,              -- { "toolName": true/false, ... }
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),

  UNIQUE (agent_id, plugin_id)
);
CREATE INDEX agent_plugin_overrides_agent_idx ON agent_plugin_overrides(agent_id);
```

Semantics:
- **No row** → agent uses the default (all tools from the plugin are available).
- **Row with `enabled = false`** → plugin is fully disabled for this agent.
- **Row with `enabled = true` and `tool_overrides`** → only the tools marked `true` in the JSONB map are enabled; anything `false` or absent is disabled.

This keeps the schema additive (no changes to existing tables) and company-scope-compatible (agent already has `company_id`).

### 3.2 Drizzle schema

```ts
// packages/db/src/schema/agent_plugin_overrides.ts
import { pgTable, uuid, boolean, timestamp, jsonb, index, uniqueIndex } from "drizzle-orm/pg-core";
import { agents } from "./agents.js";
import { plugins } from "./plugins.js";

export const agentPluginOverrides = pgTable(
  "agent_plugin_overrides",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    agentId: uuid("agent_id").notNull().references(() => agents.id, { onDelete: "cascade" }),
    pluginId: uuid("plugin_id").notNull().references(() => plugins.id, { onDelete: "cascade" }),
    enabled: boolean("enabled").notNull().default(true),
    toolOverrides: jsonb("tool_overrides").$type<Record<string, boolean>>(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => ({
    agentIdx: index("agent_plugin_overrides_agent_idx").on(table.agentId),
    agentPluginUq: uniqueIndex("agent_plugin_overrides_agent_plugin_uq").on(table.agentId, table.pluginId),
  }),
);
```

Export from `packages/db/src/schema/index.ts`.

---

## 4. API Surface

### 4.1 New endpoints (all under `/api`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/agents/:agentId/plugin-overrides` | List all plugin overrides for this agent |
| `PUT` | `/agents/:agentId/plugin-overrides/:pluginId` | Create/update override for a specific plugin |
| `DELETE` | `/agents/:agentId/plugin-overrides/:pluginId` | Remove override (revert to default) |
| `GET` | `/agents/:agentId/available-tools` | List tools available to this agent after filtering |

### 4.2 Response shapes

**`GET /agents/:agentId/plugin-overrides`**
```ts
type AgentPluginOverrideResponse = {
  pluginId: string;
  pluginKey: string;
  displayName: string;
  enabled: boolean;
  /** null = all tools enabled; otherwise map of tool name → enabled */
  toolOverrides: Record<string, boolean> | null;
  /** Full list of tools declared by this plugin (for UI rendering) */
  declaredTools: Array<{
    name: string;           // namespaced name
    displayName: string;
    description: string;
  }>;
}[];
```

**`GET /agents/:agentId/available-tools`**
Returns `AgentToolDescriptor[]` — same shape as `GET /plugins/tools` but filtered through the agent's overrides. This is what the tool dispatcher uses at runtime.

### 4.3 Tool dispatch integration

Modify `PluginToolDispatcher.listToolsForAgent()` to accept an optional `agentId` parameter:

```ts
listToolsForAgent(filter?: ToolListFilter & { agentId?: string }): AgentToolDescriptor[]
```

When `agentId` is provided:
1. Load `agent_plugin_overrides` for the agent (cache with short TTL or event-based invalidation).
2. Filter out plugins where `enabled = false`.
3. For plugins with `tool_overrides`, filter out tools where the override is `false`.
4. Return the remaining tools.

The `POST /plugins/tools/execute` endpoint already receives `runContext.agentId` — add a guard that checks the agent's overrides before dispatching.

---

## 5. UI Design

### 5.1 New tab: "Plugins"

Add `"plugins"` to the `AgentDetailView` type and the tab bar:

```ts
type AgentDetailView = "dashboard" | "configuration" | "skills" | "plugins" | "runs" | "budget";
```

Route: `/agents/:agentRef/plugins`

### 5.2 Layout (top to bottom)

```
┌──────────────────────────────────────────────┐
│  Agent Plugin Configuration                  │
│  "Control which plugins and tools this       │
│   agent can access."                         │
├──────────────────────────────────────────────┤
│                                              │
│           ┌─────────────┐                    │
│    ┌──────┤  Agent Node  ├──────┐            │
│    │      └──────┬──────┘      │            │
│    ▼             ▼             ▼            │
│  ┌─────┐    ┌─────┐      ┌─────┐          │
│  │Jira │    │ GH  │      │Figma│          │
│  │ ✓   │    │ ✓   │      │ ✗   │          │
│  └─────┘    └─────┘      └─────┘          │
│                                              │
│  [Click a plugin node to see its tools]      │
│                                              │
├──────────────────────────────────────────────┤
│  Selected: GitHub                            │
│  ┌──────────────────────────────────┐        │
│  │ ☑ github:search-issues           │        │
│  │ ☑ github:create-issue            │        │
│  │ ☐ github:close-issue             │        │
│  │ ☑ github:list-prs                │        │
│  └──────────────────────────────────┘        │
└──────────────────────────────────────────────┘
```

### 5.3 Graph Visualisation

**Library:** Use `d3-force` (d3's force-directed graph layout) with SVG rendering. No heavy framework dependency — just `d3-force` + `d3-selection` for the layout math, rendered as React-controlled SVG.

Install: `pnpm --filter @paperclipai/ui add d3-force d3-selection` + `@types/d3-force @types/d3-selection` as devDeps.

**Graph structure:**
- **Centre node:** The agent — shows avatar/icon + name
- **Satellite nodes:** One per installed plugin — shows plugin icon + name + enabled/disabled state
- **Edges:** Lines from agent to each plugin, colour-coded:
  - Green solid line → plugin enabled
  - Grey dashed line → plugin disabled
- **Node styling:**
  - Enabled plugin: bright border, full opacity
  - Disabled plugin: muted, reduced opacity, dashed border
  - Hovered/selected: glow effect, scale up slightly
- **Interaction:**
  - Click a plugin node → toggles enable/disable (with optimistic update)
  - Click again or click "expand" → shows tool detail panel below the graph
  - Drag nodes to rearrange (d3-force handles this naturally)

### 5.4 Tool detail panel

When a plugin node is selected, a panel appears below the graph:

- Plugin name + description + enabled toggle (master switch)
- Tool list with individual checkboxes
- "Enable all" / "Disable all" bulk actions
- Changes auto-save with debounce (PUT to the override endpoint)
- Toast confirmation on save

### 5.5 File structure

```
ui/src/
  components/
    agent-plugin-graph/
      AgentPluginGraph.tsx         # Main graph component (d3-force SVG)
      AgentNode.tsx                # Centre agent node
      PluginNode.tsx               # Satellite plugin nodes
      PluginEdge.tsx               # Connection lines
      ToolDetailPanel.tsx          # Expandable tool list
      use-force-layout.ts          # d3-force simulation hook
      types.ts                     # Graph node/edge types
  pages/
    AgentDetail.tsx                # Add "plugins" tab + PluginsTab component
  api/
    agent-plugin-overrides.ts      # API client functions
```

---

## 6. Server Changes

### 6.1 New route file

```
server/src/routes/agent-plugin-overrides.ts
```

Mounted at `/api/agents/:agentId/plugin-overrides` and `/api/agents/:agentId/available-tools`.

Access control:
- Board access required (same as agent routes)
- Company access check via the agent's `company_id`
- Activity log entries for mutations

### 6.2 New service

```
server/src/services/agent-plugin-overrides.ts
```

Functions:
- `listOverrides(agentId)` — joins `agent_plugin_overrides` with `plugins` to return enriched records
- `upsertOverride(agentId, pluginId, { enabled, toolOverrides })` — upsert with `onConflictDoUpdate`
- `deleteOverride(agentId, pluginId)` — delete the row
- `getEffectiveTools(agentId)` — returns the filtered tool list after applying overrides

### 6.3 Tool dispatcher changes

In `plugin-tool-dispatcher.ts`:
- Add optional `agentId` to `ToolListFilter`
- When `agentId` is present, query `agent_plugin_overrides` and filter the tool list
- Add a runtime guard in `executeTool()` that checks whether the tool is allowed for the agent before dispatching

---

## 7. Shared Types

Add to `packages/shared/src/validators/`:

```ts
export const agentPluginOverrideSchema = z.object({
  pluginId: z.string().uuid(),
  enabled: z.boolean(),
  toolOverrides: z.record(z.boolean()).nullable().optional(),
});
```

Export from `packages/shared/src/index.ts`.

---

## 8. Implementation Order

| Phase | Work | Files |
|---|---|---|
| **1 — Schema** | Create `agent_plugin_overrides` table, export, generate migration | `packages/db/src/schema/agent_plugin_overrides.ts`, `packages/db/src/schema/index.ts` |
| **2 — Service** | Implement `agent-plugin-overrides` service | `server/src/services/agent-plugin-overrides.ts` |
| **3 — Routes** | Implement REST endpoints, mount in `app.ts` | `server/src/routes/agent-plugin-overrides.ts`, `server/src/app.ts` |
| **4 — Tool filtering** | Wire agent overrides into `PluginToolDispatcher` | `server/src/services/plugin-tool-dispatcher.ts` |
| **5 — API client** | Add frontend API functions | `ui/src/api/agent-plugin-overrides.ts` |
| **6 — Graph component** | Build the d3-force graph component | `ui/src/components/agent-plugin-graph/` |
| **7 — Tab integration** | Add "Plugins" tab to `AgentDetail.tsx` | `ui/src/pages/AgentDetail.tsx` |
| **8 — Shared types** | Add validators + types to shared package | `packages/shared/` |
| **9 — Tests** | Unit tests for service, route, and dispatcher filtering | `server/src/__tests__/` |
| **10 — Verify** | `pnpm -r typecheck && pnpm test:run && pnpm build` | — |

---

## 9. Open Questions

1. **Cascading defaults:** If a plugin is disabled at the company level (`plugin_company_settings.enabled = false`), should it even appear in the agent's graph? **Proposed:** Yes, but greyed out with a "disabled by company" label — cannot be enabled at agent level.

2. **Persist vs. session:** Should tool toggle changes save immediately (auto-save) or require an explicit Save button? **Proposed:** Auto-save with debounce + undo toast (consistent with modern toggle UIs).

3. **Default state:** When no override row exists, should the UI show all tools as enabled? **Proposed:** Yes — absence of an override means "use defaults" which is "everything on."

4. **Skills tab:** The existing "Skills" tab is commented out. Should the new "Plugins" tab subsume its functionality (showing both skills and plugin tools)? **Proposed:** Keep them separate — Skills = instruction bundles, Plugins = external integrations with tools.

---

## 10. Non-Goals (V1)

- Per-tool parameter restrictions (e.g., "allow search but only for project X")
- Plugin tool usage analytics per agent
- Drag-and-drop reordering of tool priority
- Plugin marketplace browsing from the agent tab
- Multi-agent bulk configuration

---

## 11. Risks

| Risk | Mitigation |
|---|---|
| d3-force bundle size | `d3-force` is ~15 KB gzipped; acceptable for a feature page. Tree-shake by importing only `d3-force` and `d3-selection`, not all of d3. |
| N+1 query on override lookups during tool dispatch | Cache agent overrides in the service with a 30s TTL, invalidated on write. |
| SVG rendering performance with many plugins | Force layout limits to installed plugins (typically <20); not a concern. |
| Migration on existing deployments | Additive table only, no changes to existing schema. Fully backwards-compatible. |
