/// <reference types="vite/client" />
/// <reference types="@testing-library/jest-dom" />

interface ImportMetaEnv {
  /** Public API Gateway base URL, e.g. `http://localhost:8000`. */
  readonly VITE_API_GATEWAY_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
