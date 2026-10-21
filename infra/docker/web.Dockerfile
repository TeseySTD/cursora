# syntax=docker/dockerfile:1
# Nginx image that serves the built admin SPA and widget.js. Build context: repository root.

# ---- build: admin + widget static files ----
# 24.22.1 (.nvmrc) has no amd64 image yet; bump when published.
FROM node:24.22.0-trixie-slim AS build
ENV PNPM_HOME=/pnpm \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
WORKDIR /src

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/widget/package.json apps/widget/
COPY apps/admin/package.json apps/admin/
# The api-client `prepare` script generates the TS client from openapi.json during install.
COPY packages/api-client/package.json packages/api-client/openapi.json packages/api-client/openapi-ts.config.ts packages/api-client/
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store \
    pnpm install --frozen-lockfile --store-dir /pnpm/store

COPY tsconfig.base.json ./
COPY packages/api-client packages/api-client
COPY apps/widget apps/widget
COPY apps/admin apps/admin
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN pnpm --filter @cursora/widget build && pnpm --filter @cursora/admin build

# ---- runtime: nginx with static files ----
FROM nginx:1.31.7-alpine
COPY infra/nginx/nginx.conf /etc/nginx/nginx.conf
COPY infra/nginx/conf.d/ /etc/nginx/conf.d/
COPY --from=build /src/apps/admin/dist/ /usr/share/nginx/html/admin/
COPY --from=build /src/apps/widget/dist/widget.js /usr/share/nginx/html/widget/widget.js
EXPOSE 8080 8081
