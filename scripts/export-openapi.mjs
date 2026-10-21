// pnpm api:openapi — FastAPI schema -> packages/api-client/openapi.json -> generated TS client.
import { run } from "./lib.mjs";

run("uv", ["run", "--package", "cursora-api", "python", "apps/api/scripts/export_openapi.py"]);
run("pnpm", ["--filter", "@cursora/api-client", "generate"]);
