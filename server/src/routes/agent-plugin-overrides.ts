/**
 * @fileoverview Routes for per-agent plugin and tool overrides.
 *
 * Mounted under `/api/agents/:agentId/plugin-overrides` and
 * `/api/agents/:agentId/available-tools`.
 *
 * @see doc/plans/2026-03-20-agent-plugin-configuration.md
 */

import { Router } from "express";
import { eq } from "drizzle-orm";
import type { Db } from "@paperclipai/db";
import { agents } from "@paperclipai/db";
import { upsertAgentPluginOverrideSchema } from "@paperclipai/shared";
import {
  agentPluginOverrideService,
  logActivity,
} from "../services/index.js";
import { assertBoard, assertCompanyAccess, getActorInfo } from "./authz.js";
import { notFound } from "../errors.js";
import type { PluginToolDispatcher } from "../services/plugin-tool-dispatcher.js";

export interface AgentPluginOverrideRouteDeps {
  toolDispatcher?: PluginToolDispatcher;
}

export function agentPluginOverrideRoutes(db: Db, deps: AgentPluginOverrideRouteDeps = {}) {
  const router = Router();
  const svc = agentPluginOverrideService(db);

  /** Resolve agent and assert company access. */
  async function resolveAgent(req: import("express").Request, agentId: string) {
    assertBoard(req);
    const [agent] = await db
      .select({ id: agents.id, companyId: agents.companyId, name: agents.name })
      .from(agents)
      .where(eq(agents.id, agentId));
    if (!agent) throw notFound("Agent not found");
    assertCompanyAccess(req, agent.companyId);
    return agent;
  }

  // =========================================================================
  // GET /agents/:agentId/plugin-overrides
  // =========================================================================

  /**
   * List all installed plugins with their override state for this agent.
   * Returns one entry per ready plugin, whether or not an explicit override
   * row exists.
   */
  router.get("/agents/:agentId/plugin-overrides", async (req, res) => {
    const agent = await resolveAgent(req, req.params.agentId);
    const overrides = await svc.listForAgent(agent.id);
    res.json(overrides);
  });

  // =========================================================================
  // PUT /agents/:agentId/plugin-overrides/:pluginId
  // =========================================================================

  /**
   * Create or update a plugin override for the agent.
   *
   * Body: `{ enabled: boolean, toolOverrides?: Record<string, boolean> | null }`
   */
  router.put("/agents/:agentId/plugin-overrides/:pluginId", async (req, res) => {
    const agent = await resolveAgent(req, req.params.agentId);
    const { pluginId } = req.params;

    const parsed = upsertAgentPluginOverrideSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ error: parsed.error.flatten() });
      return;
    }

    const result = await svc.upsert(agent.id, pluginId, parsed.data);

    const actor = getActorInfo(req);
    await logActivity(db, {
      companyId: agent.companyId,
      actorType: actor.actorType,
      actorId: actor.actorId,
      action: "agent_plugin_override.upsert",
      entityType: "agent",
      entityId: agent.id,
      details: { pluginId, enabled: parsed.data.enabled },
    });

    res.json(result);
  });

  // =========================================================================
  // DELETE /agents/:agentId/plugin-overrides/:pluginId
  // =========================================================================

  /**
   * Remove a plugin override, reverting the agent to defaults (all tools enabled).
   */
  router.delete("/agents/:agentId/plugin-overrides/:pluginId", async (req, res) => {
    const agent = await resolveAgent(req, req.params.agentId);
    const { pluginId } = req.params;
    const removed = await svc.remove(agent.id, pluginId);

    if (removed) {
      const actor = getActorInfo(req);
      await logActivity(db, {
        companyId: agent.companyId,
        actorType: actor.actorType,
        actorId: actor.actorId,
        action: "agent_plugin_override.delete",
        entityType: "agent",
        entityId: agent.id,
        details: { pluginId },
      });
    }

    res.json({ ok: true, removed });
  });

  // =========================================================================
  // GET /agents/:agentId/available-tools
  // =========================================================================

  /**
   * List tools available to the agent after applying plugin/tool overrides.
   * If no tool dispatcher is configured, returns 501.
   */
  router.get("/agents/:agentId/available-tools", async (req, res) => {
    const agent = await resolveAgent(req, req.params.agentId);

    if (!deps.toolDispatcher) {
      res.status(501).json({ error: "Plugin tool dispatch is not enabled" });
      return;
    }

    // Get all tools, then filter by agent overrides
    const allTools = deps.toolDispatcher.listToolsForAgent();
    const disabled = await svc.getDisabledTools(agent.id);

    if (!disabled) {
      // No overrides — all tools available
      res.json(allTools);
      return;
    }

    const filtered = allTools.filter((t) => !disabled.has(t.name));
    res.json(filtered);
  });

  return router;
}
