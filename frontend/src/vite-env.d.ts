/// <reference types="vite/client" />
/// <reference types="@testing-library/jest-dom" />

interface ImportMetaEnv {
  /** Data service / gateway base URL, e.g. `http://localhost:8001`. */
  readonly VITE_API_BASE_URL?: string
  /** Gateway price stream URL, e.g. `ws://localhost:8001/api/v1/btc/price/stream`. */
  readonly VITE_PRICE_WS_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
