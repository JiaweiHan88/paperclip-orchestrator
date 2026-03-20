/**
 * Types for the agent-plugin graph visualisation.
 */

import type { SimulationNodeDatum } from "d3-force";

export interface PluginToolNode {
  name: string;
  displayName: string;
  description: string;
  enabled: boolean;
}

export interface PluginGraphNode extends SimulationNodeDatum {
  id: string;
  type: "agent" | "plugin" | "tool";
  label: string;
  pluginKey?: string;
  pluginId?: string;
  enabled?: boolean;
  /** Only on tool nodes — short tool name. */
  toolName?: string;
  /** Only on plugin nodes — number of declared tools. */
  toolCount?: number;
  /** Only on plugin nodes — nested tools. */
  tools?: PluginToolNode[];
  /** Agent icon emoji or URL. */
  icon?: string | null;
}

export interface PluginGraphEdge {
  source: string;
  target: string;
  enabled: boolean;
}
