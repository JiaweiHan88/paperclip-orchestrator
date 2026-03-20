import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    projects: ["packages/db", "packages/adapter-utils", "packages/adapters/opencode-local", "packages/plugins/examples/plugin-jira", "server", "ui", "cli"],
  },
});
