// pnpm skills:outdated — list vendored skills whose upstream folder changed after the commit
// pinned in their SOURCE.md. Only reports: re-import and review the diff by hand (AGENTS.md).
// Uses the GitHub REST API; set GITHUB_TOKEN if the unauthenticated rate limit (60/h) runs out.
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { repoRoot } from "./lib.mjs";

const skillsDir = join(repoRoot, ".claude", "skills");
const headers = { Accept: "application/vnd.github+json", "User-Agent": "cursora-skills-outdated" };
if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;

async function github(path) {
  const response = await fetch(`https://api.github.com${path}`, { headers });
  if (!response.ok) throw new Error(`GitHub API answered ${response.status} for ${path}`);
  return response.json();
}

// SOURCE.md keeps the origin in a table: Upstream (a GitHub tree link), Path and Commit.
function readSource(file) {
  const text = readFileSync(file, "utf8");
  const upstream = text.match(
    /\| Upstream\s+\|.*\(https:\/\/github\.com\/([^/]+)\/([^/]+)\/tree\//,
  );
  const path = text.match(/\| Path\s+\| `([^`]+)`/);
  const commit = text.match(/\| Commit\s+\| `([0-9a-f]{40})`/);
  if (!upstream || !path || !commit) return null;
  return { owner: upstream[1], repo: upstream[2], path: path[1], commit: commit[1] };
}

let outdated = 0;
let failed = 0;

for (const name of readdirSync(skillsDir).sort()) {
  const file = join(skillsDir, name, "SOURCE.md");
  // Project skills and the OpenSpec-generated ones have no SOURCE.md.
  if (!existsSync(file)) continue;
  const source = readSource(file);
  if (!source) {
    console.error(`${name}: SOURCE.md has no Upstream, Path or Commit row`);
    failed++;
    continue;
  }
  const { owner, repo, path, commit } = source;
  const short = commit.slice(0, 7);
  try {
    // The repository moves on all the time; only commits that touch the skill's folder count.
    const query = new URLSearchParams({ path, per_page: "1" });
    const [latest] = await github(`/repos/${owner}/${repo}/commits?${query}`);
    if (!latest) throw new Error(`no commit on the default branch touches ${path}`);
    const status =
      latest.sha === commit
        ? "identical"
        : (await github(`/repos/${owner}/${repo}/compare/${commit}...${latest.sha}`)).status;
    if (status === "ahead") {
      outdated++;
      console.log(
        `${name}: ${path} changed after ${short}: ` +
          `https://github.com/${owner}/${repo}/compare/${commit}...${latest.sha}`,
      );
    } else if (status === "identical" || status === "behind") {
      console.log(`${name}: up to date (${short})`);
    } else {
      throw new Error(`pinned commit ${short} is not on the default branch (${status})`);
    }
  } catch (error) {
    console.error(`${name}: ${error.message}`);
    failed++;
  }
}

if (outdated) {
  console.log(`\n${outdated} skill(s) changed upstream; re-import and review the diff.`);
}
process.exit(outdated || failed ? 1 : 0);
