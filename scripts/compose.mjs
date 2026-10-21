// Wrapper around `docker compose` with the repo's compose files.
//   node scripts/compose.mjs prod <args...>   -> compose.yml
//   node scripts/compose.mjs dev  <args...>   -> compose.yml + compose.dev.yml
// The root .env (if present) is used for variable interpolation.
import { existsSync } from "node:fs";
import { join } from "node:path";
import { repoRoot, run } from "./lib.mjs";

const [profile, ...args] = process.argv.slice(2);
const files = { prod: ["compose.yml"], dev: ["compose.yml", "compose.dev.yml"] }[profile];
if (!files) {
  console.error("usage: node scripts/compose.mjs <prod|dev> <docker compose args...>");
  process.exit(1);
}

const composeDir = join("infra", "compose");
const fileArgs = files.flatMap((f) => ["-f", join(composeDir, f)]);
const envFile = join(repoRoot, ".env");
const envArgs = existsSync(envFile) ? ["--env-file", envFile] : [];

run("docker", ["compose", ...fileArgs, ...envArgs, ...args]);
