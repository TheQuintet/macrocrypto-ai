/** Single public entry point for data and alert requests. */
export const API_GATEWAY_BASE_URL = import.meta.env.VITE_API_GATEWAY_BASE_URL

/**
 * Legacy direct Data Service URL.
 *
 * Used only when no gateway URL is configured, so existing local setups keep
 * working while deployed and full-stack runs use the gateway.
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

/** Legacy direct Alert Service URL. */
export const ALERT_API_BASE_URL = import.meta.env.VITE_ALERT_API_BASE_URL

/**
 * Alert-service notification stream. Unset → no notification HTTP or live
 * stream; the inbox uses simulated data instead.
 */
export const NOTIFICATION_STREAM_URL = import.meta.env
  .VITE_NOTIFICATION_STREAM_URL

function joinBaseUrl(base: string | undefined, path: string) {
  if (!base) {
    return null
  }

  return `${base.replace(/\/+$/, '')}${path}`
}

export function isApiConfigured() {
  return Boolean(API_GATEWAY_BASE_URL || API_BASE_URL)
}

export function isAlertApiConfigured() {
  return Boolean(API_GATEWAY_BASE_URL || ALERT_API_BASE_URL)
}

export function isNotificationApiConfigured() {
  return Boolean(NOTIFICATION_STREAM_URL)
}

/** Gateway URL for a data path, falling back to the legacy direct service. */
export function apiUrl(path: string) {
  return joinBaseUrl(API_GATEWAY_BASE_URL || API_BASE_URL, path)
}

/** Gateway URL for an alert path, falling back to the legacy direct service. */
export function alertApiUrl(path: string) {
  return joinBaseUrl(API_GATEWAY_BASE_URL || ALERT_API_BASE_URL, path)
}
