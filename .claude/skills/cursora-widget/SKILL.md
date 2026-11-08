---
name: cursora-widget
description: Build and change the embeddable Cursora widget (apps/widget) — React 19 inside a Shadow DOM, Tailwind CSS v4 and shadcn/ui styles confined to the shadow root, Radix portals targeting the shadow root, a single IIFE widget.js with a size budget, and Vitest tests that assert inside the shadow root. Use for any UI, styling, shadcn component, signal-collection, build or bundle-size change under apps/widget/.
---

# Widget (`apps/widget`)

Customer sites embed it with `<script src=".../widget/widget.js" data-site-key="...">`. It runs
inside pages we do not control, so isolation, size and privacy matter more than in the admin.

## How it is wired

- `src/main.tsx` — IIFE entry; reads `data-site-key` from `document.currentScript` and mounts.
- `src/mount.tsx` — creates the `<cursora-widget>` host element, attaches a shadow root,
  injects the compiled CSS (`styles.css?inline`) as a `<style>` inside the shadow root, and
  renders React plus a `[data-cursora-portal]` container.
- `plugins/shadow-dom-css.ts` — PostCSS pass after Tailwind: `:root` → `:host`, `@property`
  fallbacks, `rem` → `px` (so host-page font sizes cannot rescale the widget).
- `src/lib/portal.tsx` — `usePortalContainer()`.

## Rules

- CSS stays inside the shadow root: never inject styles into `document.head`, never rely on
  host-page CSS or global selectors, never use `document.querySelector` for widget elements
  (query the shadow root).
- Every shadcn/Radix component that renders a Portal (Popover, Tooltip, Dialog, Select,
  DropdownMenu, HoverCard, ...) must pass `container={usePortalContainer()}` — copy the
  pattern from `src/components/ui/popover.tsx`. Otherwise it renders into `document.body`,
  unstyled and outside the widget.
- Add shadcn components from `apps/widget` with the shadcn CLI already in devDependencies
  (`pnpm exec shadcn add <component>`), then patch the portal container and run the tests.
- Bundle size: one IIFE, no code splitting. Justify every new dependency; check with
  `pnpm analyze:widget` (treemap at `apps/widget/dist/stats.html`) and `pnpm size:widget`
  (budget in `size-budget.config.mjs`; the gzip budget is still `TODO(team)`).
- Privacy: the widget collects behavioural signals for the risk engine; never log signals or
  device data to the console, and never send or expose a raw fingerprint — the backend
  stores only HMAC hashes. Collect only signals agreed in `docs/project-context.md`.
- Open decisions are marked `TODO(team)` (mount position, open vs closed shadow root, widget
  state machine, copy/i18n). Do not settle them silently — ask or leave the TODO.

## Tests

- Vitest + Testing Library + jsdom (`apps/widget/tests/`). Mount with `mountWidget(...)` and
  query inside the shadow root: `within(shadowRoot as unknown as HTMLElement)`.
- Keep the isolation tests green: no CSS in `document.head`, no `:root` in the injected CSS,
  portals inside `[data-cursora-portal]`.
- `pnpm test:widget`, `pnpm --filter @cursora/widget typecheck`, then `pnpm check`.

## Dev loop

`pnpm dev:widget` serves the test harness on <http://localhost:5174> (`index.html`,
`src/dev.tsx`).
