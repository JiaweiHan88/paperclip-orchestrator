import type {
  PluginPageProps,
  PluginSettingsPageProps,
  PluginWidgetProps,
  PluginSidebarProps,
  PluginDetailTabProps,
} from "@paperclipai/plugin-sdk/ui";
import { usePluginData, usePluginAction } from "@paperclipai/plugin-sdk/ui";

// ---------------------------------------------------------------------------
// Page — /:companyPrefix/jira
// ---------------------------------------------------------------------------

export function JiraPage({ context }: PluginPageProps) {
  const { data, loading, error } = usePluginData<{
    lastSyncAt: string | null;
    errorCount: number;
    configured: boolean;
  }>("sync-status");

  const triggerSync = usePluginAction("trigger-sync");

  return (
    <section aria-label="Jira integration">
      <h2>Jira Integration</h2>
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

export function JiraSettingsPage(_props: PluginSettingsPageProps) {
  return (
    <section aria-label="Jira settings">
      <h2>Jira Plugin Settings</h2>
      <p>Configure your Jira connection in the auto-generated form above.</p>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Dashboard widget
// ---------------------------------------------------------------------------

export function JiraDashboardWidget({ context }: PluginWidgetProps) {
  const { data } = usePluginData<{
    lastSyncAt: string | null;
    errorCount: number;
    configured: boolean;
  }>("sync-status");

  return (
    <section aria-label="Jira sync status">
      <strong>Jira</strong>
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

export function JiraSidebarLink(_props: PluginSidebarProps) {
  return <span>Jira</span>;
}

// ---------------------------------------------------------------------------
// Issue detail tab
// ---------------------------------------------------------------------------

export function JiraIssueTab({ context }: PluginDetailTabProps) {
  const { data } = usePluginData("linked-issue", { issueId: context.entityId });

  return (
    <section aria-label="Jira linked issue">
      <h3>Linked Jira Issue</h3>
      {data ? <pre>{JSON.stringify(data, null, 2)}</pre> : <p>No linked Jira issue.</p>}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Project detail tab
// ---------------------------------------------------------------------------

export function JiraProjectTab({ context }: PluginDetailTabProps) {
  return (
    <section aria-label="Jira project mapping">
      <h3>Jira Project Mapping</h3>
      <p>Project: {context.entityId}</p>
      <p>Configure project-to-Jira-project mappings in plugin settings.</p>
    </section>
  );
}
