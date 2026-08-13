/**
 * Base URL of the data service (or the gateway, once it fronts it).
 *
 * Unset in a frontend-only run — no backend, no Docker. Callers fall back to
 * simulated data in that case, and mark it as such so it is never mistaken
 * for the real market.
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export function isApiConfigured() {
  return Boolean(API_BASE_URL)
}

/** Absolute URL for an API path, or `null` when no backend is configured. */
export function apiUrl(path: string) {
  if (!API_BASE_URL) {
    return null
  }

  return `${API_BASE_URL.replace(/\/+$/, '')}${path}`
}
