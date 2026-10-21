// pnpm api:check — regenerate the contract and fail if anything under packages/api-client changed.
import { capture, run } from "./lib.mjs";

const scope = "packages/api-client";

run("node", ["scripts/export-openapi.mjs"]);

// --porcelain also reports new untracked files, which a plain `git diff` would miss.
const status = capture("git", ["status", "--porcelain", "--", scope]).trim();
if (status) {
  console.error(`\nAPI contract is stale. Run \`pnpm api:openapi\` and commit:\n${status}`);
  run("git", ["--no-pager", "diff", "--stat", "--", scope], { allowFailure: true });
  process.exit(1);
}
console.log("API contract is up to date.");
