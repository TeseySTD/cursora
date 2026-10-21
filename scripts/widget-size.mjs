// Prints the raw and gzipped size of the built widget as a Markdown table (used in CI job summary).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { gzipSync } from "node:zlib";
import { repoRoot } from "./lib.mjs";

const file = join(repoRoot, "apps", "widget", "dist", "widget.js");
const bytes = readFileSync(file);
const kib = (n) => `${(n / 1024).toFixed(1)} KiB`;

console.log("| file | raw | gzip |");
console.log("| --- | --- | --- |");
console.log(`| widget.js | ${kib(bytes.length)} | ${kib(gzipSync(bytes, { level: 9 }).length)} |`);
