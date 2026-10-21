import "@testing-library/jest-dom/vitest";

// jsdom lacks ResizeObserver, which Radix popper-based components (Popover) use.
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};
