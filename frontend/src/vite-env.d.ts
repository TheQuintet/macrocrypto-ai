/// <reference types="vite/client" />
/// <reference types="@testing-library/jest-dom" />

interface ImportMetaEnv {
  /** Public API Gateway base URL, e.g. `http://localhost:8000`. */
  readonly VITE_API_GATEWAY_BASE_URL?: string
  /** Legacy direct Data Service base URL, e.g. `http://localhost:8001`. */
  readonly VITE_API_BASE_URL?: string
  /** Legacy direct Alert Service base URL, e.g. `http://localhost:8003`. */
  readonly VITE_ALERT_API_BASE_URL?: string
  /** Gateway price stream URL, e.g. `ws://localhost:8001/api/v1/btc/price/stream`. */
  readonly VITE_PRICE_WS_URL?: string
  /** Alert-service notification SSE or WebSocket URL. Unset → simulated inbox, no notification HTTP. */
  readonly VITE_NOTIFICATION_STREAM_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
