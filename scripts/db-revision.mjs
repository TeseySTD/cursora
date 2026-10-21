// pnpm db:revision "add sites table" — alembic revision --autogenerate -m <msg>.
import { run } from "./lib.mjs";

const message = process.argv.slice(2).join(" ").trim();
if (!message) {
  console.error('usage: pnpm db:revision "<message>"');
  process.exit(1);
}
run("uv", [
  "run",
  "--package",
  "cursora-api",
  "alembic",
  "-c",
  "apps/api/alembic.ini",
  "revision",
  "--autogenerate",
  "-m",
  message,
]);
