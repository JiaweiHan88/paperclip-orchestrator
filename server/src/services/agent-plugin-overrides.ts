/**
 * @fileoverview Service for managing per-agent plugin and tool overrides.
 *
 * Provides CRUD operations on the `agent_plugin_overrides` table and a
 * query to compute the effective tool list for a given agent after applying
 * plugin/tool overrides.
 *
 * @see doc/plans/2026-03-20-agent-plugin-configuration.md
 */

import { and, eq } from "drizzle-orm";
import type { Db } from "@paperclipai/db";
import { agentPluginOverrides, plugins } from "@paperclipai/db";
import type { PaperclipPluginManifestV1 } from "@paperclipai/shared";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** A declared tool from a plugin manifest, enriched with plugin context. */
export interface DeclaredTool {
  /** Namespaced tool name (e.g. `"acme.jira:search-issues"`). */
  name: string;
  displayName: string;
  description: string;
}

/** A full override record joined with plugin metadata. */
export interface AgentPluginOverrideRecord {
  pluginId: string;
  pluginKey: string;
  displayName: string;
  enabled: boolean;
  toolOverrides: Record<string, boolean> | null;
  declaredTools: DeclaredTool[];
}

// ---------------------------------------------------------------------------
// Service factory
// ---------------------------------------------------------------------------

export function agentPluginOverrideService(db: Db) {
  /**
   * List all plugin overrides for an agent, enriched with plugin metadata
   * and the full list of declared tools from the plugin manifest.
   *
   * Returns one entry per installed plugin (in `ready` status), regardless
   * of whether an explicit override row exists. If no override exists the
   * plugin defaults to `enabled: true, toolOverrides: null`.
   */
  async function listForAgent(agentId: string): Promise<AgentPluginOverrideRecord[]> {
    // 1. Get all ready plugins
    const readyPlugins = await db
      .select()
      .from(plugins)
      .where(eq(plugins.status, "ready"));

    // 2. Get existing overrides for this agent
    const overrides = await db
      .select()
      .from(agentPluginOverrides)
      .where(eq(agentPluginOverrides.agentId, agentId));

    const overrideMap = new Map(
      overrides.map((o) => [o.pluginId, o]),
    );

    // 3. Join them into enriched records
    return readyPlugins.map((plugin) => {
      const manifest = plugin.manifestJson as PaperclipPluginManifestV1 | null;
      const override = overrideMap.get(plugin.id);
      const tools: DeclaredTool[] = (manifest?.tools ?? []).map((t) => ({
        name: `${manifest!.id}:${t.name}`,
        displayName: t.displayName,
        description: t.description,
      }));

      return {
        pluginId: plugin.id,
        pluginKey: plugin.pluginKey,
        displayName: manifest?.displayName ?? plugin.pluginKey,
        enabled: override ? override.enabled : true,
        toolOverrides: override?.toolOverrides as Record<string, boolean> | null ?? null,
        declaredTools: tools,
      };
    });
  }

  /**
   * Create or update an override for a specific (agent, plugin) pair.
   */
  async function upsert(
    agentId: string,
    pluginId: string,
    data: { enabled: boolean; toolOverrides?: Record<string, boolean> | null },
  ) {
    const existing = await db
      .select()
      .from(agentPluginOverrides)
      .where(
        and(
          eq(agentPluginOverrides.agentId, agentId),
          eq(agentPluginOverrides.pluginId, pluginId),
        ),
      )
      .then((rows) => rows[0] ?? null);

    if (existing) {
      await db
        .update(agentPluginOverrides)
        .set({
          enabled: data.enabled,
          toolOverrides: data.toolOverrides ?? null,
          updatedAt: new Date(),
        })
        .where(eq(agentPluginOverrides.id, existing.id));
      return { ...existing, enabled: data.enabled, toolOverrides: data.toolOverrides ?? null };
    }

    const [created] = await db
      .insert(agentPluginOverrides)
      .values({
        agentId,
        pluginId,
        enabled: data.enabled,
        toolOverrides: data.toolOverrides ?? null,
      })
      .returning();
    return created;
  }

  /**
   * Remove an override for a specific (agent, plugin) pair, reverting to
   * the default "everything enabled" state.
   */
  async function remove(agentId: string, pluginId: string): Promise<boolean> {
    const result = await db
      .delete(agentPluginOverrides)
      .where(
        and(
          eq(agentPluginOverrides.agentId, agentId),
          eq(agentPluginOverrides.pluginId, pluginId),
        ),
      )
      .returning();
    return result.length > 0;
  }

  /**
   * Build a set of disabled tool names for an agent. Used by the tool
   * dispatcher to filter the tool list at runtime.
   *
   * Returns `null` if no overrides exist (meaning everything is enabled).
   * Otherwise returns a `Set<string>` of namespaced tool names that are
   * disabled, plus the full set of tool names for plugins that are entirely
   * disabled.
   */
  async function getDisabledTools(agentId: string): Promise<Set<string> | null> {
    const overrides = await db
      .select({
        pluginId: agentPluginOverrides.pluginId,
        enabled: agentPluginOverrides.enabled,
        toolOverrides: agentPluginOverrides.toolOverrides,
        pluginKey: plugins.pluginKey,
        manifestJson: plugins.manifestJson,
      })
      .from(agentPluginOverrides)
      .innerJoin(plugins, eq(plugins.id, agentPluginOverrides.pluginId))
      .where(eq(agentPluginOverrides.agentId, agentId));

    if (overrides.length === 0) return null;

    const disabled = new Set<string>();

    for (const row of overrides) {
      const manifest = row.manifestJson as PaperclipPluginManifestV1 | null;
      const declaredTools = (manifest?.tools ?? []).map((t) => `${manifest!.id}:${t.name}`);

      if (!row.enabled) {
        // Entire plugin is disabled → disable all its tools
        for (const toolName of declaredTools) {
          disabled.add(toolName);
        }
        continue;
      }

      // Plugin enabled but has per-tool overrides
      const toolOv = row.toolOverrides as Record<string, boolean> | null;
      if (toolOv) {
        for (const toolName of declaredTools) {
          if (toolOv[toolName] === false) {
            disabled.add(toolName);
          }
        }
      }
    }

    return disabled.size > 0 ? disabled : null;
  }

  return {
    listForAgent,
    upsert,
    remove,
    getDisabledTools,
  };
}
