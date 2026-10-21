import { configureApiClient } from "@cursora/api-client";

/** Base URL of the Cursora API; "/api" goes through the Vite dev proxy or Nginx. */
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL || "/api";

export function configureApi(): void {
  configureApiClient(API_BASE_URL);
}
