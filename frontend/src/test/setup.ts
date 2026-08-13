import '@testing-library/jest-dom/vitest'

// jsdom does not implement ResizeObserver, and Radix popper-based primitives
// (tooltip, sheet, sidebar) construct one on mount.
if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}
