// Public entry point. Everything under ./generated is generated from openapi.json
// (on `pnpm install`, before build/typecheck/test, and by `pnpm api:openapi`) and is not committed.
import { client } from "./generated/client.gen";

export * from "./generated";
export { client };

/** Point the generated client at the API (e.g. "/api" behind Nginx or the Vite dev proxy). */
export function configureApiClient(baseUrl: string): void {
  client.setConfig({ baseUrl });
}
