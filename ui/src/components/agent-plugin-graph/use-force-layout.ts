/**
 * React hook that runs a d3-force simulation and returns updated node positions.
 *
 * Supports three tiers: agent (center) → plugin → tool.
 * Tool nodes are pushed outward from the center to create an "exploding" effect.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  type Simulation,
  type SimulationLinkDatum,
} from "d3-force";
import type { PluginGraphNode, PluginGraphEdge } from "./types";

interface SimLink extends SimulationLinkDatum<PluginGraphNode> {
  source: string | PluginGraphNode;
  target: string | PluginGraphNode;
  enabled: boolean;
}

interface UseForceLayoutOptions {
  width: number;
  height: number;
  nodes: PluginGraphNode[];
  edges: PluginGraphEdge[];
}

/**
 * Custom force that pushes tool nodes radially away from the center.
 * This creates the "exploding" effect where tools fan out behind their plugin.
 */
function forceRadialPush(cx: number, cy: number, strength: number) {
  let nodes: PluginGraphNode[] = [];

  function force(alpha: number) {
    for (const node of nodes) {
      if (node.type !== "tool") continue;
      const dx = (node.x ?? cx) - cx;
      const dy = (node.y ?? cy) - cy;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      // Push outward
      node.vx = (node.vx ?? 0) + (dx / dist) * strength * alpha;
      node.vy = (node.vy ?? 0) + (dy / dist) * strength * alpha;
    }
  }

  force.initialize = (n: PluginGraphNode[]) => { nodes = n; };

  return force;
}

export function useForceLayout({ width, height, nodes, edges }: UseForceLayoutOptions) {
  const simRef = useRef<Simulation<PluginGraphNode, SimLink> | null>(null);
  const [positions, setPositions] = useState<PluginGraphNode[]>([]);

  const tick = useCallback(() => {
    if (!simRef.current) return;
    const current = simRef.current.nodes();
    setPositions(current.map((n) => ({ ...n })));
  }, []);

  useEffect(() => {
    if (width === 0 || height === 0) return;

    const cx = width / 2;
    const cy = height / 2;

    // Deep-copy nodes so d3 can mutate x/y
    const simNodes: PluginGraphNode[] = nodes.map((n) => ({ ...n }));
    const simLinks: SimLink[] = edges.map((e) => ({ ...e }));

    // Pin the agent node in the center
    const agentNode = simNodes.find((n) => n.type === "agent");
    if (agentNode) {
      agentNode.fx = cx;
      agentNode.fy = cy;
    }

    const sim = forceSimulation<PluginGraphNode>(simNodes)
      .force(
        "link",
        forceLink<PluginGraphNode, SimLink>(simLinks)
          .id((d) => d.id)
          .distance((link) => {
            const src = typeof link.source === "object" ? link.source : simNodes.find((n) => n.id === link.source);
            const tgt = typeof link.target === "object" ? link.target : simNodes.find((n) => n.id === link.target);
            if (src?.type === "tool" || tgt?.type === "tool") return 70;
            return 160;
          })
          .strength((link) => {
            const src = typeof link.source === "object" ? link.source : simNodes.find((n) => n.id === link.source);
            const tgt = typeof link.target === "object" ? link.target : simNodes.find((n) => n.id === link.target);
            if (src?.type === "tool" || tgt?.type === "tool") return 0.8;
            return 0.5;
          }),
      )
      .force("charge", forceManyBody().strength((d) => {
        const node = d as PluginGraphNode;
        if (node.type === "tool") return -60;
        if (node.type === "plugin") return -350;
        return -500;
      }))
      .force("center", forceCenter(cx, cy).strength(0.05))
      .force("collide", forceCollide<PluginGraphNode>((d) => {
        if (d.type === "tool") return 60;
        if (d.type === "plugin") return 80;
        return 50;
      }))
      // Push tool nodes outward from center — the "exploding" effect
      .force("radialPush", forceRadialPush(cx, cy, 30) as unknown as ReturnType<typeof forceManyBody>)
      .alphaDecay(0.025)
      .on("tick", tick);

    simRef.current = sim;

    return () => {
      sim.stop();
      simRef.current = null;
    };
  }, [width, height, nodes, edges, tick]);

  return positions;
}
