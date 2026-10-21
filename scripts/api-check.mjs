// pnpm api:check — re-export openapi.json from FastAPI and fail if it differs from the commit.
// The TS client is generated from openapi.json on install and is not committed, so only the
// contract itself is checked here (no Node dependencies needed).
import { capture, run } from "./lib.mjs";

const contract = "packages/api-client/openapi.json";

run("uv", ["run", "--package", "cursora-api", "python", "apps/api/scripts/export_openapi.py"]);

// --porcelain also reports the file as untracked, which a plain `git diff` would miss.
const status = capture("git", ["status", "--porcelain", "--", contract]).trim();
if (status) {
  console.error(`\nAPI contract is stale. Run \`pnpm api:openapi\` and commit:\n${status}`);
  run("git", ["--no-pager", "diff", "--stat", "--", contract], { allowFailure: true });
  process.exit(1);
}
console.log("API contract is up to date.");
