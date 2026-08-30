/**
 * Base URL of the data service (or the gateway, once it fronts it).
 *
 * Unset in a frontend-only run — no backend, no Docker. Callers fall back to
 * simulated data in that case, and mark it as such so it is never mistaken
 * for the real market.
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

/** Base URL of the alert service (price-alert CRUD, notifications). */
export const ALERT_API_BASE_URL = import.meta.env.VITE_ALERT_API_BASE_URL

function joinBaseUrl(base: string | undefined, path: string) {
  if (!base) {
    return null
  }

  return `${base.replace(/\/+$/, '')}${path}`
}

export function isApiConfigured() {
  return Boolean(API_BASE_URL)
}

export function isAlertApiConfigured() {
  return Boolean(ALERT_API_BASE_URL)
}

/** Absolute URL for a data-service path, or `null` when none is configured. */
export function apiUrl(path: string) {
  return joinBaseUrl(API_BASE_URL, path)
}

/** Absolute URL for an alert-service path, or `null` when none is configured. */
export function alertApiUrl(path: string) {
  return joinBaseUrl(ALERT_API_BASE_URL, path)
}
