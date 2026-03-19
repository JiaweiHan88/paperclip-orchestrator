import type {
  PluginPageProps,
  PluginSettingsPageProps,
  PluginWidgetProps,
  PluginSidebarProps,
  PluginDetailTabProps,
} from "@paperclipai/plugin-sdk/ui";
import { usePluginData, usePluginAction } from "@paperclipai/plugin-sdk/ui";

// ---------------------------------------------------------------------------
// Page — /:companyPrefix/gerrit
// ---------------------------------------------------------------------------

export function GerritPage({ context }: PluginPageProps) {
  const { data, loading, error } = usePluginData<{
    lastSyncAt: string | null;
    errorCount: number;
    configured: boolean;
  }>("sync-status");

  const triggerSync = usePluginAction("trigger-sync");

  return (
    <section aria-label="Gerrit integration">
      <h2>Gerrit Code Review</h2>
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

export function GerritSettingsPage(_props: PluginSettingsPageProps) {
  return (
    <section aria-label="Gerrit settings">
      <h2>Gerrit Plugin Settings</h2>
      <p>Configure your Gerrit connection in the auto-generated form above.</p>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Dashboard widget
// ---------------------------------------------------------------------------

export function GerritDashboardWidget({ context }: PluginWidgetProps) {
  const { data } = usePluginData<{
    lastSyncAt: string | null;
    errorCount: number;
    configured: boolean;
  }>("sync-status");

  return (
    <section aria-label="Gerrit review status">
      <strong>Gerrit</strong>
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

export function GerritSidebarLink(_props: PluginSidebarProps) {
  return <span>Gerrit</span>;
}

// ---------------------------------------------------------------------------
// Issue detail tab
// ---------------------------------------------------------------------------

export function GerritIssueTab({ context }: PluginDetailTabProps) {
  const { data } = usePluginData("linked-change", { issueId: context.entityId });

  return (
    <section aria-label="Gerrit linked change">
      <h3>Linked Gerrit Change</h3>
      {data ? <pre>{JSON.stringify(data, null, 2)}</pre> : <p>No linked Gerrit change.</p>}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Project detail tab
// ---------------------------------------------------------------------------

export function GerritProjectTab({ context }: PluginDetailTabProps) {
  return (
    <section aria-label="Gerrit project mapping">
      <h3>Gerrit Project Mapping</h3>
      <p>Project: {context.entityId}</p>
      <p>Configure project-to-Gerrit-project mappings in plugin settings.</p>
    </section>
  );
}
