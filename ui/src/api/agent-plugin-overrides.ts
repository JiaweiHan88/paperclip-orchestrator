/**
 * @fileoverview Frontend API client for per-agent plugin/tool overrides.
 *
 * @see server/src/routes/agent-plugin-overrides.ts
 */

import { api } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DeclaredTool {
  name: string;
  displayName: string;
  description: string;
}

export interface AgentToolDescriptor {
  name: string;
  displayName: string;
  description: string;
  parametersSchema: Record<string, unknown>;
  pluginId: string;
}

export interface AgentPluginOverrideRecord {
  pluginId: string;
  pluginKey: string;
  displayName: string;
  enabled: boolean;
  toolOverrides: Record<string, boolean> | null;
  declaredTools: DeclaredTool[];
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export const agentPluginOverridesApi = {
  /**
   * List all plugins and their override state for an agent.
   */
  list: (agentId: string) =>
    api.get<AgentPluginOverrideRecord[]>(`/agents/${agentId}/plugin-overrides`),

  /**
   * Create or update a plugin override for an agent.
   */
  upsert: (
    agentId: string,
    pluginId: string,
    data: { enabled: boolean; toolOverrides?: Record<string, boolean> | null },
  ) => api.put<unknown>(`/agents/${agentId}/plugin-overrides/${pluginId}`, data),

  /**
   * Remove a plugin override (revert to defaults).
   */
  remove: (agentId: string, pluginId: string) =>
    api.delete<{ ok: boolean; removed: boolean }>(
      `/agents/${agentId}/plugin-overrides/${pluginId}`,
    ),

  /**
   * List tools available to the agent after filtering.
   */
  availableTools: (agentId: string) =>
    api.get<AgentToolDescriptor[]>(`/agents/${agentId}/available-tools`),
};
