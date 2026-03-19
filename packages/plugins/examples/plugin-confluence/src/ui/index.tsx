import type {
  PluginPageProps,
  PluginSettingsPageProps,
  PluginWidgetProps,
  PluginSidebarProps,
  PluginDetailTabProps,
} from "@paperclipai/plugin-sdk/ui";
import { usePluginData, usePluginAction } from "@paperclipai/plugin-sdk/ui";

// ---------------------------------------------------------------------------
// Page — /:companyPrefix/confluence
// ---------------------------------------------------------------------------

export function ConfluencePage({ context }: PluginPageProps) {
  const { data, loading, error } = usePluginData<{
    lastSyncAt: string | null;
    errorCount: number;
    indexedPages: number;
    configured: boolean;
  }>("sync-status");

  const triggerSync = usePluginAction("trigger-sync");

  return (
    <section aria-label="Confluence integration">
      <h2>Confluence Knowledge Base</h2>
      {loading && <p>Loading sync status…</p>}
      {error && <p>Error loading sync status.</p>}
      {data && (
        <div>
          <p>Configured: {data.configured ? "Yes" : "No — configure in plugin settings"}</p>
          <p>Indexed pages: {data.indexedPages}</p>
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

export function ConfluenceSettingsPage(_props: PluginSettingsPageProps) {
  return (
    <section aria-label="Confluence settings">
      <h2>Confluence Plugin Settings</h2>
      <p>Configure your Confluence connection in the auto-generated form above.</p>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Dashboard widget
// ---------------------------------------------------------------------------

export function ConfluenceDashboardWidget({ context }: PluginWidgetProps) {
  const { data } = usePluginData<{
    lastSyncAt: string | null;
    errorCount: number;
    indexedPages: number;
    configured: boolean;
  }>("sync-status");

  return (
    <section aria-label="Confluence sync status">
      <strong>Confluence</strong>
      {data ? (
        <div>
          <div>Indexed: {data.indexedPages} pages</div>
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

export function ConfluenceSidebarLink(_props: PluginSidebarProps) {
  return <span>Confluence</span>;
}

// ---------------------------------------------------------------------------
// Issue detail tab
// ---------------------------------------------------------------------------

export function ConfluenceIssueTab({ context }: PluginDetailTabProps) {
  const { data } = usePluginData("linked-pages", { issueId: context.entityId });

  return (
    <section aria-label="Confluence linked pages">
      <h3>Linked Confluence Pages</h3>
      {Array.isArray(data) && data.length > 0 ? (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      ) : (
        <p>No linked Confluence pages.</p>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Project detail tab
// ---------------------------------------------------------------------------

export function ConfluenceProjectTab({ context }: PluginDetailTabProps) {
  return (
    <section aria-label="Confluence project space">
      <h3>Confluence Space</h3>
      <p>Project: {context.entityId}</p>
      <p>Configure space-to-project mappings in plugin settings to surface relevant documentation here.</p>
    </section>
  );
}
