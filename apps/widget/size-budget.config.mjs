// Size budget for dist/widget.js, checked by `pnpm size:widget` (and in CI).
export default {
  // TODO(team): agree on the gzip budget in KiB (gzip level 9). null = no budget yet.
  gzipKiB: null,
  // "warn": report only (CI warning annotation). "error": fail the check when over budget.
  mode: "warn",
};
