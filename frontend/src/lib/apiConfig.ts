/** Single public entry point for every HTTP request. */
export const API_GATEWAY_BASE_URL = import.meta.env.VITE_API_GATEWAY_BASE_URL

function joinBaseUrl(base: string | undefined, path: string) {
  if (!base) {
    return null
  }

  return `${base.replace(/\/+$/, '')}${path}`
}

function toWebSocketUrl(httpUrl: string) {
  return httpUrl.replace(/^http/, 'ws')
}

export function isApiGatewayConfigured() {
  return Boolean(API_GATEWAY_BASE_URL)
}

/** Gateway URL for a path. Unset → callers use simulated data. */
export function apiUrl(path: string) {
  return joinBaseUrl(API_GATEWAY_BASE_URL, path)
}

/** Gateway WebSocket URL for a path (`http` → `ws`, `https` → `wss`). */
export function wsUrl(path: string) {
  const url = apiUrl(path)
  return url ? toWebSocketUrl(url) : null
}
