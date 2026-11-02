// Size budget for dist/widget.js, checked by `pnpm size:widget` (and in CI).
export default {
  // Gzip budget in KiB (gzip level 9). null = no budget.
  gzipKiB: 40,
  // "warn": report only (CI warning annotation). "error": fail the check when over budget.
  mode: "error",
};
