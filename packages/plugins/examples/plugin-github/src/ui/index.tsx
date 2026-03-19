import type {
  PluginPageProps,
  PluginSettingsPageProps,
  PluginWidgetProps,
  PluginSidebarProps,
  PluginDetailTabProps,
} from "@paperclipai/plugin-sdk/ui";
import { usePluginData, usePluginAction } from "@paperclipai/plugin-sdk/ui";

// ---------------------------------------------------------------------------
// Page — /:companyPrefix/github
// ---------------------------------------------------------------------------

export function GitHubPage({ context }: PluginPageProps) {
  const { data, loading, error } = usePluginData<{
    lastSyncAt: string | null;
    errorCount: number;
    configured: boolean;
  }>("sync-status");

  const triggerSync = usePluginAction("trigger-sync");

  return (
    <section aria-label="GitHub integration">
      <h2>GitHub Integration</h2>
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

export function GitHubSettingsPage(_props: PluginSettingsPageProps) {
  return (
    <section aria-label="GitHub settings">
      <h2>GitHub Plugin Settings</h2>
      <p>Configure your GitHub connection in the auto-generated form above.</p>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Dashboard widget
// ---------------------------------------------------------------------------

export function GitHubDashboardWidget({ context }: PluginWidgetProps) {
  const { data } = usePluginData<{
    lastSyncAt: string | null;
    errorCount: number;
    configured: boolean;
  }>("sync-status");

  return (
    <section aria-label="GitHub sync status">
      <strong>GitHub</strong>
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

export function GitHubSidebarLink(_props: PluginSidebarProps) {
  return <span>GitHub</span>;
}

// ---------------------------------------------------------------------------
// Issue detail tab
// ---------------------------------------------------------------------------

export function GitHubIssueTab({ context }: PluginDetailTabProps) {
  const { data: linked } = usePluginData("linked-issue", { issueId: context.entityId });
  const { data: prs } = usePluginData("linked-prs", { issueId: context.entityId });

  return (
    <section aria-label="GitHub linked issue">
      <h3>Linked GitHub Issue</h3>
      {linked ? <pre>{JSON.stringify(linked, null, 2)}</pre> : <p>No linked GitHub issue.</p>}
      <h3>Linked Pull Requests</h3>
      {Array.isArray(prs) && prs.length > 0 ? (
        <pre>{JSON.stringify(prs, null, 2)}</pre>
      ) : (
        <p>No linked PRs.</p>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Project detail tab
// ---------------------------------------------------------------------------

export function GitHubProjectTab({ context }: PluginDetailTabProps) {
  return (
    <section aria-label="GitHub project mapping">
      <h3>GitHub Repo Mapping</h3>
      <p>Project: {context.entityId}</p>
      <p>Configure project-to-repo mappings in plugin settings.</p>
    </section>
  );
}
