/**
 * ToolDetailPanel — expandable panel showing individual tools for a selected plugin.
 */

import { cn } from "@/lib/utils";
import type { PluginToolNode } from "./types";

interface ToolDetailPanelProps {
  pluginKey: string;
  displayName: string;
  pluginEnabled: boolean;
  tools: PluginToolNode[];
  onTogglePlugin: (enabled: boolean) => void;
  onToggleTool: (toolName: string, enabled: boolean) => void;
  onClose: () => void;
}

export function ToolDetailPanel({
  pluginKey,
  displayName,
  pluginEnabled,
  tools,
  onTogglePlugin,
  onToggleTool,
  onClose,
}: ToolDetailPanelProps) {
  const allEnabled = tools.every((t) => t.enabled);
  const noneEnabled = tools.every((t) => !t.enabled);

  return (
    <div className="border border-border rounded-lg bg-card p-4 space-y-3 animate-in fade-in-0 slide-in-from-top-2 duration-200">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm">{displayName}</span>
          <span className="text-xs text-muted-foreground font-mono">{pluginKey}</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Master toggle */}
          <button
            type="button"
            onClick={() => onTogglePlugin(!pluginEnabled)}
            className={cn(
              "relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors",
              pluginEnabled ? "bg-emerald-500" : "bg-muted",
            )}
            role="switch"
            aria-checked={pluginEnabled}
            aria-label={`Toggle ${displayName}`}
          >
            <span
              className={cn(
                "pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition-transform",
                pluginEnabled ? "translate-x-4" : "translate-x-0",
              )}
            />
          </button>
          <button
            type="button"
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-xs"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
      </div>

      {!pluginEnabled && (
        <p className="text-xs text-muted-foreground">
          Plugin disabled for this agent. Enable it to configure individual tools.
        </p>
      )}

      {pluginEnabled && tools.length === 0 && (
        <p className="text-xs text-muted-foreground">
          This plugin does not declare any agent tools.
        </p>
      )}

      {/* Tool list */}
      {pluginEnabled && tools.length > 0 && (
        <div className="space-y-1">
          {/* Bulk actions */}
          <div className="flex items-center gap-2 pb-1">
            <button
              type="button"
              className="text-xs text-muted-foreground hover:text-foreground underline"
              onClick={() => tools.forEach((t) => !t.enabled && onToggleTool(t.name, true))}
              disabled={allEnabled}
            >
              Enable all
            </button>
            <span className="text-muted-foreground text-xs">·</span>
            <button
              type="button"
              className="text-xs text-muted-foreground hover:text-foreground underline"
              onClick={() => tools.forEach((t) => t.enabled && onToggleTool(t.name, false))}
              disabled={noneEnabled}
            >
              Disable all
            </button>
          </div>

          {tools.map((tool) => (
            <label
              key={tool.name}
              className="flex items-start gap-2 rounded-md px-2 py-1.5 hover:bg-muted/50 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={tool.enabled}
                onChange={(e) => onToggleTool(tool.name, e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-border accent-emerald-500"
              />
              <div className="min-w-0">
                <div className="text-sm font-mono truncate">{tool.name}</div>
                <div className="text-xs text-muted-foreground truncate">
                  {tool.description || tool.displayName}
                </div>
              </div>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
