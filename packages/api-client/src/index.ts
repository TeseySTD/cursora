// Public entry point. Everything under ./generated is produced by `pnpm api:openapi`.
import { client } from "./generated/client.gen";

export * from "./generated";
export { client };

/** Point the generated client at the API (e.g. "/api" behind Nginx or the Vite dev proxy). */
export function configureApiClient(baseUrl: string): void {
  client.setConfig({ baseUrl });
}
