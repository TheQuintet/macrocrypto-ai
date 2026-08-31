import { isAlertApiConfigured } from '@/lib/apiConfig'

/**
 * Frontend-only (no `VITE_ALERT_API_BASE_URL`) uses simulated notifications.
 * When an alert backend *is* configured but the notification HTTP API is
 * missing, we still simulate so the inbox can be used. Price-alert CRUD does
 * not use this — live failures there propagate like prices.
 */
export async function withSimulatedFallback<T>(
  live: () => Promise<T>,
  simulate: () => Promise<T>,
): Promise<T> {
  if (!isAlertApiConfigured()) {
    return simulate()
  }

  try {
    return await live()
  } catch {
    return simulate()
  }
}
