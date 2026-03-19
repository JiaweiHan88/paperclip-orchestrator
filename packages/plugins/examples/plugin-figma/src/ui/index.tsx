import type {
  PluginPageProps,
  PluginSettingsPageProps,
  PluginWidgetProps,
  PluginSidebarProps,
  PluginDetailTabProps,
} from "@paperclipai/plugin-sdk/ui";
import { usePluginData, usePluginAction } from "@paperclipai/plugin-sdk/ui";

// ---------------------------------------------------------------------------
// Page — /:companyPrefix/figma
// ---------------------------------------------------------------------------

export function FigmaPage({ context }: PluginPageProps) {
  const { data, loading, error } = usePluginData<{
    lastSyncAt: string | null;
    errorCount: number;
    configured: boolean;
  }>("sync-status");

  const triggerSync = usePluginAction("trigger-sync");

  return (
    <section aria-label="Figma integration">
      <h2>Figma Designs</h2>
      {loading && <p>Loading sync status…</p>}
      {error && <p>Error loading sync status.</p>}
      {data && (
        <div>
          <p>Configured: {data.configured ? "Yes" : "No — configure in plugin settings"}</p>
          <p>Last sync: {data.lastSyncAt ?? "never"}</p>
          <p>Errors: {data.errorCount}</p>
          <button type="button" onClick={() => triggerSync({})}>
            Sync now
          </button>
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Settings page
// ---------------------------------------------------------------------------

export function FigmaSettingsPage(_props: PluginSettingsPageProps) {
  return (
    <section aria-label="Figma settings">
      <h2>Figma Plugin Settings</h2>
      <p>Configure your Figma connection in the auto-generated form above.</p>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Dashboard widget
// ---------------------------------------------------------------------------

export function FigmaDashboardWidget({ context }: PluginWidgetProps) {
  const { data } = usePluginData<{
    lastSyncAt: string | null;
    errorCount: number;
    configured: boolean;
  }>("sync-status");

  return (
    <section aria-label="Figma design status">
      <strong>Figma</strong>
      {data ? (
        <div>
          <div>Last sync: {data.lastSyncAt ?? "never"}</div>
          {data.errorCount > 0 && <div>⚠ {data.errorCount} sync error(s)</div>}
        </div>
      ) : (
        <div>Loading…</div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Sidebar link
// ---------------------------------------------------------------------------

export function FigmaSidebarLink(_props: PluginSidebarProps) {
  return <span>Figma</span>;
}

// ---------------------------------------------------------------------------
// Issue detail tab
// ---------------------------------------------------------------------------

export function FigmaIssueTab({ context }: PluginDetailTabProps) {
  const { data } = usePluginData("linked-designs", { issueId: context.entityId });

  return (
    <section aria-label="Figma linked designs">
      <h3>Linked Figma Designs</h3>
      {Array.isArray(data) && data.length > 0 ? (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      ) : (
        <p>No linked Figma designs.</p>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Project detail tab
// ---------------------------------------------------------------------------

export function FigmaProjectTab({ context }: PluginDetailTabProps) {
  return (
    <section aria-label="Figma project files">
      <h3>Figma Project Files</h3>
      <p>Project: {context.entityId}</p>
      <p>Design files linked to this project will appear here once sync is configured.</p>
    </section>
  );
}
