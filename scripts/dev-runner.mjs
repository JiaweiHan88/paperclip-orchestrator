#!/usr/bin/env node
import { spawn } from "node:child_process";
import { createInterface } from "node:readline/promises";
import { stdin, stdout } from "node:process";

const mode = process.argv[2] === "watch" ? "watch" : "dev";
const cliArgs = process.argv.slice(3);

const tailscaleAuthFlagNames = new Set([
  "--tailscale-auth",
  "--authenticated-private",
]);

let tailscaleAuth = false;
const forwardedArgs = [];

for (const arg of cliArgs) {
  if (tailscaleAuthFlagNames.has(arg)) {
    tailscaleAuth = true;
    continue;
  }
  forwardedArgs.push(arg);
}

if (process.env.npm_config_tailscale_auth === "true") {
  tailscaleAuth = true;
}
if (process.env.npm_config_authenticated_private === "true") {
  tailscaleAuth = true;
}

const env = {
  ...process.env,
  PAPERCLIP_UI_DEV_MIDDLEWARE: "true",
};

if (mode === "watch") {
  env.PAPERCLIP_MIGRATION_PROMPT ??= "never";
  env.PAPERCLIP_MIGRATION_AUTO_APPLY ??= "true";
}

if (tailscaleAuth) {
  env.PAPERCLIP_DEPLOYMENT_MODE = "authenticated";
  env.PAPERCLIP_DEPLOYMENT_EXPOSURE = "private";
  env.PAPERCLIP_AUTH_BASE_URL_MODE = "auto";
  env.HOST = "0.0.0.0";
  console.log("[paperclip] dev mode: authenticated/private (tailscale-friendly) on 0.0.0.0");
} else {
  console.log("[paperclip] dev mode: local_trusted (default)");
}

const pnpmBin = process.platform === "win32" ? "pnpm.cmd" : "pnpm";

function toError(error, context = "Dev runner command failed") {
  if (error instanceof Error) return error;
  if (error === undefined) return new Error(context);
  if (typeof error === "string") return new Error(`${context}: ${error}`);

  try {
    return new Error(`${context}: ${JSON.stringify(error)}`);
  } catch {
    return new Error(`${context}: ${String(error)}`);
  }
}

process.on("uncaughtException", (error) => {
  const err = toError(error, "Uncaught exception in dev runner");
  process.stderr.write(`${err.stack ?? err.message}\n`);
  process.exit(1);
});

process.on("unhandledRejection", (reason) => {
  const err = toError(reason, "Unhandled promise rejection in dev runner");
  process.stderr.write(`${err.stack ?? err.message}\n`);
  process.exit(1);
});

function formatPendingMigrationSummary(migrations) {
  if (migrations.length === 0) return "none";
  return migrations.length > 3
    ? `${migrations.slice(0, 3).join(", ")} (+${migrations.length - 3} more)`
    : migrations.join(", ");
}

async function runPnpm(args, options = {}) {
  return await new Promise((resolve, reject) => {
    const child = spawn(pnpmBin, args, {
      stdio: options.stdio ?? ["ignore", "pipe", "pipe"],
      env: options.env ?? process.env,
      shell: process.platform === "win32",
    });

    let stdoutBuffer = "";
    let stderrBuffer = "";

    if (child.stdout) {
      child.stdout.on("data", (chunk) => {
        stdoutBuffer += String(chunk);
      });
    }
    if (child.stderr) {
      child.stderr.on("data", (chunk) => {
        stderrBuffer += String(chunk);
      });
    }

    child.on("error", reject);
    child.on("exit", (code, signal) => {
      resolve({
        code: code ?? 0,
        signal,
        stdout: stdoutBuffer,
        stderr: stderrBuffer,
      });
    });
  });
}

async function maybePreflightMigrations() {
  if (mode !== "watch") return;

  const status = await runPnpm(
    ["--filter", "@paperclipai/db", "exec", "tsx", "src/migration-status.ts", "--json"],
    { env },
  );
  if (status.code !== 0) {
    process.stderr.write(
      status.stderr ||
        status.stdout ||
        `[paperclip] Command failed with code ${status.code}: pnpm --filter @paperclipai/db exec tsx src/migration-status.ts --json\n`,
    );
    process.exit(status.code);
  }

  let payload;
  try {
    payload = JSON.parse(status.stdout.trim());
  } catch (error) {
    process.stderr.write(
      status.stderr ||
        status.stdout ||
        "[paperclip] migration-status returned invalid JSON payload\n",
    );
    throw toError(error, "Unable to parse migration-status JSON output");
  }

  if (payload.status !== "needsMigrations" || payload.pendingMigrations.length === 0) {
    return;
  }

  const autoApply = env.PAPERCLIP_MIGRATION_AUTO_APPLY === "true";
  let shouldApply = autoApply;

  if (!autoApply) {
    if (!stdin.isTTY || !stdout.isTTY) {
      shouldApply = true;
    } else {
      const prompt = createInterface({ input: stdin, output: stdout });
      try {
        const answer = (
          await prompt.question(
            `Apply pending migrations (${formatPendingMigrationSummary(payload.pendingMigrations)}) now? (y/N): `,
          )
        )
          .trim()
          .toLowerCase();
        shouldApply = answer === "y" || answer === "yes";
      } finally {
        prompt.close();
      }
    }
  }

  if (!shouldApply) {
    process.stderr.write(
      `[paperclip] Pending migrations detected (${formatPendingMigrationSummary(payload.pendingMigrations)}). ` +
        "Refusing to start watch mode against a stale schema.\n",
    );
    process.exit(1);
  }

  const migrate = spawn(pnpmBin, ["db:migrate"], {
    stdio: "inherit",
    env,
    shell: process.platform === "win32",
  });
  const exit = await new Promise((resolve) => {
    migrate.on("exit", (code, signal) => resolve({ code: code ?? 0, signal }));
  });
  if (exit.signal) {
    process.kill(process.pid, exit.signal);
    return;
  }
  if (exit.code !== 0) {
    process.exit(exit.code);
  }
}

await maybePreflightMigrations();

async function buildPluginSdk() {
  console.log("[paperclip] building plugin sdk...");
  const result = await runPnpm(
    ["--filter", "@paperclipai/plugin-sdk", "build"],
    { stdio: "inherit" },
  );
  if (result.signal) {
    process.kill(process.pid, result.signal);
    return;
  }
  if (result.code !== 0) {
    console.error("[paperclip] plugin sdk build failed");
    process.exit(result.code);
  }
}

await buildPluginSdk();

// ---------------------------------------------------------------------------
// Optionally start the AI tools bridge (Python sidecar)
// ---------------------------------------------------------------------------

let bridgeChild = null;

async function maybeStartBridge() {
  // Skip if explicitly disabled
  if (process.env.AI_TOOLS_BRIDGE_DISABLED === "true") return;
  // Skip if a remote bridge URL is configured
  if (process.env.AI_TOOLS_BRIDGE_URL && !process.env.AI_TOOLS_BRIDGE_URL.includes("localhost")) return;

  // Determine if uv is available
  const uvCheck = await runPnpm([], { stdio: "pipe" }).catch(() => null);
  const uvAvailable = await new Promise((resolve) => {
    const proc = spawn("uv", ["--version"], {
      stdio: "pipe",
      shell: process.platform === "win32",
    });
    proc.on("error", () => resolve(false));
    proc.on("exit", (code) => resolve(code === 0));
  });

  if (!uvAvailable) {
    console.log("[paperclip] uv not found — skipping AI tools bridge (set AI_TOOLS_BRIDGE_URL to use a remote bridge)");
    return;
  }

  const bridgePort = process.env.AI_TOOLS_BRIDGE_PORT ?? "8000";
  const bridgeDir = new URL("../ai_tools_bridge", import.meta.url).pathname;

  console.log(`[paperclip] starting AI tools bridge on port ${bridgePort}...`);

  const bridgeEnv = {
    ...process.env,
    BRIDGE_PORT: bridgePort,
    BRIDGE_LOG_LEVEL: process.env.BRIDGE_LOG_LEVEL ?? "info",
  };

  bridgeChild = spawn(
    "uv",
    ["run", "--project", bridgeDir, "python", "-m", "ai_tools_bridge"],
    {
      stdio: ["ignore", "pipe", "pipe"],
      env: bridgeEnv,
      shell: process.platform === "win32",
      cwd: bridgeDir,
    },
  );

  bridgeChild.stdout?.on("data", (chunk) => {
    process.stdout.write(`[bridge] ${chunk}`);
  });
  bridgeChild.stderr?.on("data", (chunk) => {
    process.stderr.write(`[bridge] ${chunk}`);
  });
  bridgeChild.on("error", (err) => {
    console.error("[paperclip] AI tools bridge failed to start:", err.message);
  });
  bridgeChild.on("exit", (code, signal) => {
    if (signal) return;
    if (code !== 0) {
      console.warn(`[paperclip] AI tools bridge exited with code ${code}`);
    }
  });

  // Set the bridge URL for the server process
  env.AI_TOOLS_BRIDGE_URL = `http://localhost:${bridgePort}`;
  console.log(`[paperclip] AI tools bridge started — AI_TOOLS_BRIDGE_URL=${env.AI_TOOLS_BRIDGE_URL}`);
}

await maybeStartBridge();

const serverScript = mode === "watch" ? "dev:watch" : "dev";
const child = spawn(
  pnpmBin,
  ["--filter", "@paperclipai/server", serverScript, ...forwardedArgs],
  { stdio: "inherit", env, shell: process.platform === "win32" },
);

child.on("exit", (code, signal) => {
  // Shut down the bridge when the server exits
  if (bridgeChild && !bridgeChild.killed) {
    bridgeChild.kill();
  }
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
