// Shared helpers for the cross-platform scripts in this folder (Node built-ins only).
import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const repoRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));

/**
 * Run a command in the repo root, streaming its output; exit with its code on failure.
 * Real executables (uv, git, docker) are spawned directly; `pnpm` goes through the shell
 * because on Windows it is a .cmd shim, which Node refuses to spawn without one.
 */
export function run(cmd, args = [], { allowFailure = false } = {}) {
  const viaShell = cmd === "pnpm";
  const result = spawnSync(cmd, args, { cwd: repoRoot, stdio: "inherit", shell: viaShell });
  if (result.error) {
    console.error(`failed to start ${cmd}: ${result.error.message}`);
    process.exit(1);
  }
  if (result.status !== 0 && !allowFailure) process.exit(result.status ?? 1);
  return result.status ?? 1;
}

/** Run a command and return its stdout as a string. */
export function capture(cmd, args = []) {
  const result = spawnSync(cmd, args, { cwd: repoRoot, encoding: "utf8" });
  if (result.status !== 0) {
    process.stderr.write(result.stderr ?? "");
    process.exit(result.status ?? 1);
  }
  return result.stdout;
}
