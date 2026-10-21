// Prints the raw and gzipped size of the built widget as a Markdown table.
//   node scripts/widget-size.mjs           -> table only
//   node scripts/widget-size.mjs --check   -> table + budget check (apps/widget/size-budget.config.mjs)
// In GitHub Actions the table is also appended to the job summary and the budget result is
// emitted as an annotation.
import { appendFileSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { gzipSync } from "node:zlib";
import { repoRoot } from "./lib.mjs";

const widgetDir = join(repoRoot, "apps", "widget");
const bytes = readFileSync(join(widgetDir, "dist", "widget.js"));
const gzip = gzipSync(bytes, { level: 9 }).length;
const kib = (n) => `${(n / 1024).toFixed(1)} KiB`;

const lines = [
  "| file | raw | gzip |",
  "| --- | --- | --- |",
  `| widget.js | ${kib(bytes.length)} | ${kib(gzip)} |`,
];

const inActions = process.env.GITHUB_ACTIONS === "true";
let exitCode = 0;

if (process.argv.includes("--check")) {
  const configUrl = pathToFileURL(join(widgetDir, "size-budget.config.mjs")).href;
  const { gzipKiB, mode = "warn" } = (await import(configUrl)).default;
  let level;
  let message;
  if (gzipKiB == null) {
    level = "notice";
    message = `widget.js is ${kib(gzip)} gzip; no size budget set (apps/widget/size-budget.config.mjs).`;
  } else if (gzip > gzipKiB * 1024) {
    level = mode === "error" ? "error" : "warning";
    message = `widget.js is ${kib(gzip)} gzip, over the ${gzipKiB} KiB budget.`;
    if (mode === "error") exitCode = 1;
  } else {
    level = "notice";
    message = `widget.js is ${kib(gzip)} gzip, within the ${gzipKiB} KiB budget.`;
  }
  lines.push("", `Budget: ${message}`);
  console.log(
    inActions ? `::${level} title=Widget size budget::${message}` : `[${level}] ${message}`,
  );
}

const table = lines.join("\n");
console.log(table);
if (inActions && process.env.GITHUB_STEP_SUMMARY) {
  appendFileSync(process.env.GITHUB_STEP_SUMMARY, `### Widget bundle size\n\n${table}\n`);
}
process.exit(exitCode);
