import { isApiConfigured } from '@/lib/apiConfig'

/**
 * Frontend-only (no `VITE_API_BASE_URL`) uses simulated alerts/notifications.
 * When a backend *is* configured but the alert service is down, we still
 * simulate so the UI can be used without that extra process — unlike prices,
 * these are not live market figures.
 */
export async function withSimulatedFallback<T>(
  live: () => Promise<T>,
  simulate: () => Promise<T>,
): Promise<T> {
  if (!isApiConfigured()) {
    return simulate()
  }

  try {
    return await live()
  } catch {
    return simulate()
  }
}
