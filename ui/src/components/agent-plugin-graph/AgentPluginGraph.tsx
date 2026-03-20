/**
 * AgentPluginGraph — force-directed SVG skills graph.
 *
 * Agent avatar pinned at the centre, plugin nodes as rounded pills orbit
 * around it, tool nodes expand from enabled plugins.
 *
 * - Click a plugin pill → select it (highlights connected subgraph, dims rest)
 * - Double-click a plugin pill → toggle enable/disable
 * - Smooth animated transitions on hover, select, and state change
 * - Agent avatar area at the bottom with "N equipped" badge
 */

import { useRef, useState, useMemo, useCallback, useEffect } from "react";
import { useForceLayout } from "./use-force-layout";
import type { PluginGraphNode, PluginGraphEdge } from "./types";
import type { AgentPluginOverrideRecord } from "@/api/agent-plugin-overrides";
import { AgentIcon } from "@/components/AgentIconPicker";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const AGENT_RADIUS = 48;
const PLUGIN_PILL_W = 140;
const PLUGIN_PILL_H = 42;
const PLUGIN_PILL_RX = 21;
const TOOL_PILL_W = 110;
const TOOL_PILL_H = 30;
const TOOL_PILL_RX = 15;
const SVG_MIN_HEIGHT = 480;

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface AgentPluginGraphProps {
  agentId: string;
  agentName: string;
  agentIcon?: string | null;
  overrides: AgentPluginOverrideRecord[];
  onTogglePlugin: (pluginId: string, enabled: boolean) => void;
  onToggleTool: (pluginId: string, toolName: string, enabled: boolean) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function toolNodeId(pluginId: string, toolName: string) {
  return `tool:${pluginId}:${toolName}`;
}

function truncate(s: string, max: number) {
  return s.length > max ? s.slice(0, max - 1) + "…" : s;
}

// ---------------------------------------------------------------------------
// SVG Styles (inline for transitions — Tailwind can't animate SVG fill/opacity)
// ---------------------------------------------------------------------------

const TRANSITION_ALL = "fill 0.25s, stroke 0.25s, opacity 0.25s, filter 0.25s";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AgentPluginGraph({
  agentId,
  agentName,
  agentIcon,
  overrides,
  onTogglePlugin,
  onToggleTool: _onToggleTool,
}: AgentPluginGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: SVG_MIN_HEIGHT });
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // ── Measure container ──────────────────────────────────────────────────
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = entry.contentRect.width;
        if (w > 0) setSize({ width: w, height: Math.max(SVG_MIN_HEIGHT, w * 0.55) });
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // ── Build nodes & edges ────────────────────────────────────────────────
  const { graphNodes, graphEdges } = useMemo(() => {
    const nodes: PluginGraphNode[] = [
      { id: agentId, type: "agent", label: agentName, icon: agentIcon },
    ];
    const edges: PluginGraphEdge[] = [];

    for (const ov of overrides) {
      const toolCount = ov.declaredTools.length;
      nodes.push({
        id: ov.pluginId,
        type: "plugin",
        label: ov.displayName,
        pluginKey: ov.pluginKey,
        pluginId: ov.pluginId,
        enabled: ov.enabled,
        toolCount,
      });
      edges.push({ source: agentId, target: ov.pluginId, enabled: ov.enabled });

      if (ov.enabled) {
        for (const t of ov.declaredTools) {
          const tid = toolNodeId(ov.pluginId, t.name);
          const toolEnabled =
            ov.toolOverrides?.[t.name] !== undefined ? ov.toolOverrides[t.name] : true;
          nodes.push({
            id: tid,
            type: "tool",
            label: t.displayName || t.name.split(":").pop() || t.name,
            toolName: t.name,
            pluginId: ov.pluginId,
            enabled: toolEnabled,
          });
          edges.push({ source: ov.pluginId, target: tid, enabled: toolEnabled });
        }
      }
    }
    return { graphNodes: nodes, graphEdges: edges };
  }, [agentId, agentName, agentIcon, overrides]);

  // ── Compute connected set for selection highlighting ───────────────────
  const connectedIds = useMemo(() => {
    if (!selectedId) return null;
    const set = new Set<string>([selectedId]);
    for (const e of graphEdges) {
      if (e.source === selectedId) set.add(e.target);
      if (e.target === selectedId) set.add(e.source);
    }
    // Always include the agent
    set.add(agentId);
    // If a plugin is selected, include its tools
    for (const e of graphEdges) {
      if (set.has(e.source)) set.add(e.target);
      if (set.has(e.target)) set.add(e.source);
    }
    return set;
  }, [selectedId, graphEdges, agentId]);

  // ── Force layout ───────────────────────────────────────────────────────
  const positions = useForceLayout({
    width: size.width,
    height: size.height,
    nodes: graphNodes,
    edges: graphEdges,
  });

  // ── Handlers ───────────────────────────────────────────────────────────
  const handleNodeClick = useCallback(
    (node: PluginGraphNode, e: React.MouseEvent) => {
      if (node.type === "agent") {
        setSelectedId(null);
        return;
      }
      // Double-click toggles enable/disable
      if (e.detail === 2 && node.type === "plugin" && node.pluginId) {
        onTogglePlugin(node.pluginId, !node.enabled);
        return;
      }
      // Single-click selects/deselects
      setSelectedId((prev) => (prev === node.id ? null : node.id));
    },
    [onTogglePlugin],
  );

  // Click on canvas background deselects
  const handleSvgClick = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (e.target === e.currentTarget) setSelectedId(null);
  }, []);

  // ── Derived state ──────────────────────────────────────────────────────
  const equippedCount = overrides.filter((o) => o.enabled).length;

  // ── Render helpers ─────────────────────────────────────────────────────
  const isDimmed = (nodeId: string) => connectedIds !== null && !connectedIds.has(nodeId);
  const isEdgeDimmed = (edge: PluginGraphEdge) =>
    connectedIds !== null && (!connectedIds.has(edge.source) || !connectedIds.has(edge.target));

  return (
    <div className="space-y-3">
      {/* Graph container */}
      <div
        ref={containerRef}
        className="relative border border-border rounded-xl bg-gradient-to-b from-muted/30 to-muted/5 overflow-hidden"
        style={{ minHeight: SVG_MIN_HEIGHT }}
      >
        {size.width > 0 && (
          <svg
            width={size.width}
            height={size.height}
            viewBox={`0 0 ${size.width} ${size.height}`}
            className="select-none"
            onClick={handleSvgClick}
          >
            {/* Glow filter for selected nodes */}
            <defs>
              <filter id="glow-selected" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
              <filter id="glow-hover" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="2.5" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* ── Edges ─────────────────────────────────────────────── */}
            {graphEdges.map((edge) => {
              const s = positions.find((n) => n.id === edge.source);
              const t = positions.find((n) => n.id === edge.target);
              if (!s || !t || s.x == null || t.x == null) return null;
              const isTool = s.type === "tool" || t.type === "tool";
              const dimmed = isEdgeDimmed(edge);
              return (
                <line
                  key={`${edge.source}-${edge.target}`}
                  x1={s.x}
                  y1={s.y}
                  x2={t.x}
                  y2={t.y}
                  stroke={
                    edge.enabled
                      ? isTool ? "var(--chart-1)" : "var(--chart-2)"
                      : "var(--muted-foreground)"
                  }
                  strokeWidth={isTool ? 1 : edge.enabled ? 2.5 : 1}
                  strokeDasharray={edge.enabled ? undefined : "6 4"}
                  opacity={dimmed ? 0.08 : edge.enabled ? (isTool ? 0.5 : 0.7) : 0.25}
                  style={{ transition: "opacity 0.3s, stroke 0.3s" }}
                />
              );
            })}

            {/* ── Nodes ─────────────────────────────────────────────── */}
            {positions.map((node) => {
              const isAgent = node.type === "agent";
              const isPlugin = node.type === "plugin";
              const isTool = node.type === "tool";
              const enabled = isAgent || node.enabled !== false;
              const x = node.x ?? size.width / 2;
              const y = node.y ?? size.height / 2;
              const isHovered = node.id === hoveredId;
              const isSelected = node.id === selectedId;
              const dimmed = isDimmed(node.id);

              const nodeOpacity = dimmed ? 0.15 : enabled ? 1 : 0.5;
              const filter = isSelected
                ? "url(#glow-selected)"
                : isHovered && !dimmed
                  ? "url(#glow-hover)"
                  : undefined;

              // ── Agent node (circle with avatar) ────────────────
              if (isAgent) {
                return (
                  <g
                    key={node.id}
                    transform={`translate(${x}, ${y})`}
                    onClick={(e) => handleNodeClick(node, e)}
                    className="cursor-pointer"
                    style={{ transition: TRANSITION_ALL }}
                  >
                    <circle
                      r={AGENT_RADIUS}
                      fill="var(--primary)"
                      style={{ transition: TRANSITION_ALL }}
                    />
                    <foreignObject
                      x={-AGENT_RADIUS}
                      y={-AGENT_RADIUS}
                      width={AGENT_RADIUS * 2}
                      height={AGENT_RADIUS * 2}
                      className="pointer-events-none"
                    >
                      <div className="flex items-center justify-center w-full h-full text-primary-foreground">
                        <AgentIcon icon={agentIcon} className="h-[72px] w-[72px]" />
                      </div>
                    </foreignObject>
                    <text
                      textAnchor="middle"
                      y={AGENT_RADIUS + 18}
                      fontSize={12}
                      fontWeight={600}
                      fill="var(--foreground)"
                      className="pointer-events-none"
                    >
                      {truncate(agentName, 20)}
                    </text>
                  </g>
                );
              }

              // ── Plugin node (pill with title + tool count) ─────
              if (isPlugin) {
                const pw = PLUGIN_PILL_W;
                const ph = PLUGIN_PILL_H;
                const toolCount = node.toolCount ?? 0;
                return (
                  <g
                    key={node.id}
                    transform={`translate(${x}, ${y})`}
                    onClick={(e) => handleNodeClick(node, e)}
                    onMouseEnter={() => setHoveredId(node.id)}
                    onMouseLeave={() => setHoveredId(null)}
                    className="cursor-pointer"
                    role="button"
                    tabIndex={0}
                    filter={filter}
                    opacity={nodeOpacity}
                    style={{ transition: TRANSITION_ALL }}
                  >
                    {/* Pill background */}
                    <rect
                      x={-pw / 2}
                      y={-ph / 2}
                      width={pw}
                      height={ph}
                      rx={PLUGIN_PILL_RX}
                      fill={enabled ? "var(--card)" : "var(--muted)"}
                      stroke={
                        isSelected
                          ? "var(--chart-2)"
                          : enabled
                            ? "var(--border)"
                            : "var(--muted-foreground)"
                      }
                      strokeWidth={isSelected ? 2.5 : 1.5}
                      strokeDasharray={!enabled ? "5 3" : undefined}
                      style={{ transition: TRANSITION_ALL }}
                    />

                    {/* Title */}
                    <text
                      textAnchor="middle"
                      dominantBaseline="central"
                      y={toolCount > 0 ? -5 : 0}
                      fontSize={12}
                      fontWeight={500}
                      fill="var(--foreground)"
                      className="pointer-events-none"
                      style={{ transition: TRANSITION_ALL }}
                    >
                      {truncate(node.label, 16)}
                    </text>

                    {/* Tool count badge */}
                    {toolCount > 0 && (
                      <text
                        textAnchor="middle"
                        dominantBaseline="central"
                        y={10}
                        fontSize={10}
                        fill="var(--muted-foreground)"
                        className="pointer-events-none"
                      >
                        {toolCount} tool{toolCount !== 1 ? "s" : ""}
                      </text>
                    )}

                    {/* Enabled indicator dot */}
                    <circle
                      cx={pw / 2 - 10}
                      cy={-ph / 2 + 10}
                      r={5}
                      fill={enabled ? "oklch(0.72 0.19 149)" : "var(--muted-foreground)"}
                      stroke="var(--background)"
                      strokeWidth={1.5}
                      style={{ transition: TRANSITION_ALL }}
                    />
                  </g>
                );
              }

              // ── Tool node (smaller pill) ───────────────────────
              if (isTool) {
                const tw = TOOL_PILL_W;
                const th = TOOL_PILL_H;
                return (
                  <g
                    key={node.id}
                    transform={`translate(${x}, ${y})`}
                    onMouseEnter={() => setHoveredId(node.id)}
                    onMouseLeave={() => setHoveredId(null)}
                    className="cursor-default"
                    filter={filter}
                    opacity={nodeOpacity}
                    style={{ transition: TRANSITION_ALL }}
                  >
                    <rect
                      x={-tw / 2}
                      y={-th / 2}
                      width={tw}
                      height={th}
                      rx={TOOL_PILL_RX}
                      fill={enabled ? "color-mix(in oklch, var(--chart-1) 12%, transparent)" : "var(--muted)"}
                      stroke={enabled ? "color-mix(in oklch, var(--chart-1) 50%, transparent)" : "var(--muted-foreground)"}
                      strokeWidth={1}
                      strokeDasharray={!enabled ? "3 2" : undefined}
                      style={{ transition: TRANSITION_ALL }}
                    />
                    <text
                      textAnchor="middle"
                      dominantBaseline="central"
                      fontSize={10}
                      fill="var(--foreground)"
                      className="pointer-events-none"
                      style={{ transition: TRANSITION_ALL }}
                    >
                      {truncate(node.label, 14)}
                    </text>

                    {/* Full name tooltip on hover */}
                    {isHovered && (
                      <foreignObject
                        x={-120}
                        y={-(th / 2 + 28)}
                        width={240}
                        height={24}
                        className="pointer-events-none"
                      >
                        <div className="flex justify-center">
                          <span className="bg-popover text-popover-foreground text-[10px] px-2 py-0.5 rounded-md shadow-lg border border-border whitespace-nowrap font-mono">
                            {node.toolName || node.label}
                          </span>
                        </div>
                      </foreignObject>
                    )}
                  </g>
                );
              }

              return null;
            })}
          </svg>
        )}

        {overrides.length === 0 && size.width > 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">
              No plugins installed. Install plugins to configure agent access.
            </p>
          </div>
        )}
      </div>

      {/* ── Bottom bar: avatar + equipped count + legend ───────────────── */}
      <div className="flex items-center justify-between px-2">
        {/* Agent avatar + equipped badge */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center justify-center w-9 h-9 rounded-full bg-primary text-primary-foreground text-base font-semibold shadow-sm">
            <AgentIcon icon={agentIcon} className="h-5 w-5" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-medium">{truncate(agentName, 24)}</span>
            <span className="text-xs text-muted-foreground">
              {equippedCount} equipped
            </span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 rounded-full bg-primary" />
            Agent
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-6 h-3.5 rounded-full border border-border bg-card" />
            Plugin
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-5 h-2.5 rounded-full border border-chart-1/50 bg-chart-1/10" />
            Tool
          </span>
          <span className="hidden sm:flex items-center gap-1">
            <span className="inline-block w-4 border-t border-dashed border-muted-foreground" />
            Off
          </span>
        </div>
      </div>
    </div>
  );
}
