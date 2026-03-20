import { pgTable, uuid, boolean, timestamp, jsonb, index, uniqueIndex } from "drizzle-orm/pg-core";
import { agents } from "./agents.js";
import { plugins } from "./plugins.js";

/**
 * `agent_plugin_overrides` table — per-agent plugin and tool enable/disable
 * overrides.
 *
 * When no row exists for a given (agent, plugin) pair the default behaviour
 * applies: the plugin and all its tools are available to the agent.
 *
 * - `enabled = false` → the entire plugin is disabled for this agent.
 * - `enabled = true` with a non-null `tool_overrides` → only the tools
 *   listed as `true` in the JSONB map are enabled; anything listed as
 *   `false` (or absent) is disabled.
 * - `enabled = true` with `tool_overrides = null` → all tools enabled
 *   (explicit "keep defaults" state, useful after a prior override was
 *   partially reset).
 *
 * @see doc/plans/2026-03-20-agent-plugin-configuration.md
 */
export const agentPluginOverrides = pgTable(
  "agent_plugin_overrides",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    agentId: uuid("agent_id")
      .notNull()
      .references(() => agents.id, { onDelete: "cascade" }),
    pluginId: uuid("plugin_id")
      .notNull()
      .references(() => plugins.id, { onDelete: "cascade" }),
    /** Master switch — when false the entire plugin is disabled for this agent. */
    enabled: boolean("enabled").notNull().default(true),
    /**
     * Per-tool overrides: `{ "pluginKey:toolName": true/false }`.
     * `null` means "all tools enabled" (the default).
     */
    toolOverrides: jsonb("tool_overrides").$type<Record<string, boolean>>(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => ({
    agentIdx: index("agent_plugin_overrides_agent_idx").on(table.agentId),
    agentPluginUq: uniqueIndex("agent_plugin_overrides_agent_plugin_uq").on(
      table.agentId,
      table.pluginId,
    ),
  }),
);
